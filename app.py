from flask import Flask, render_template, request, redirect, url_for, abort, session
from functools import wraps
from werkzeug.utils import secure_filename
from flask_migrate import Migrate
import os

from models import db, Product

app = Flask(__name__)
app.secret_key = "SayGex"  # Для сесій

UPLOAD_FOLDER = "static/img"  # де будуть зберігатися завантажені файли
ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "gif"}
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///products_database.db"
db.init_app(app)
migrate = Migrate(app, db)

def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS

# Список користувачів
admins = [
    {"username": "admin", "password": "12345", "name": "Головний Адмін", "email": "admin@example.com"},
    {"username": "root", "password": "qwerty", "name": "Супер Адмін", "email": "root@example.com"}
]

# Карусель
carousel_items = [
    {
        "id": 1,
        "img": "su-27.jpg",
        "title": "Технології для нашої авіації",
        "desc": "Технології, з якими 'Привид Києва' став Легендою.",
        "text_position": "right",
        "button_text": "Переглянути продукцію",
        "button_link": "/products"
    },
    {
        "id": 2,
        "img": "fpv.jpeg",
        "title": "FPV — дрони",
        "desc": "Зброя, що змінила сучасну війну.",
        "text_position": "left",
        "button_text": "Переглянути продукцію",
        "button_link": "/products"
    },
    {
        "id": 3,
        "img": "ssu2.jpg",
        "title": "Якісне спорядження",
        "desc": "Комфорт та безпека.",
        "text_position": "center",
        "button_text": "Переглянути продукцію",
        "button_link": "/products"
    }
]

# -------------------- Декоратор -------------------- #
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get("admin_logged_in"):
            return redirect(url_for("admin"))
        return f(*args, **kwargs)
    return decorated_function

# -------------------- Routes -------------------- #

@app.route("/")
def index():
    return render_template("index.html", carousel_items=carousel_items)

@app.route("/products")
def products_page():
    products = Product.query.all()
    return render_template("products.html", products=products)

@app.route("/products/<int:product_id>")
def product_detail(product_id):
    products = Product.query.all()
    product = next((p for p in products if p.id == product_id), None)
    if not product:
        abort(404)
    return render_template("product_detail.html", product=product)

@app.route("/admin", methods=["GET", "POST"])
def admin():
    error = None
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        admin_user = next((a for a in admins if a["username"] == username and a["password"] == password), None)
        if admin_user:
            session["admin_logged_in"] = True
            session["admin_name"] = admin_user["username"]
            return redirect(url_for("admin_dashboard"))
        else:
            error = "Невірний логін або пароль"
    return render_template("admin.html", error=error)

@app.route("/admin/dashboard")
@login_required
def admin_dashboard():
    admin_name = session.get("admin_name", "Admin")
    q = request.args.get("q", "").lower()
    filtered_products = [p for p in products if q in p["name"].lower()] if q else products
    return render_template("admin_dashboard.html", products=filtered_products, admin_name=admin_name)

@app.route("/admin/admins")
@login_required
def admin_list():
    q = request.args.get("q", "").lower()
    filtered_admins = [a for a in admins if q in a["username"].lower() or q in a["name"].lower()] if q else admins
    return render_template("admin_dashboard_admins.html", admin_name=session.get("admin_name"), admins=filtered_admins)

@app.route("/admin/add_product", methods=["GET", "POST"])
@login_required
def add_product():
    if request.method == "POST":
        name = request.form.get("name")
        desc = request.form.get("desc")
        file = request.files.get("img_file")

        if name and desc and file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config["UPLOAD_FOLDER"], filename))

            new_id = max([p["id"] for p in products]) + 1 if products else 1
            products.append({"id": new_id, "name": name, "desc": desc, "img": filename})

            return redirect(url_for("admin_dashboard"))

    return render_template("add_product.html")

@app.route("/admin/edit/<int:product_id>", methods=["GET", "POST"])
@login_required
def edit_product(product_id):
    product = next((p for p in products if p["id"] == product_id), None)
    if not product:
        abort(404)

    if request.method == "POST":
        product["name"] = request.form.get("name")
        product["desc"] = request.form.get("desc")

        # Завантаження файлу
        file = request.files.get("img_file")
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config["UPLOAD_FOLDER"], filename))
            product["img"] = filename  # зберігаємо ім'я файлу в продукті

        return redirect(url_for("admin_dashboard"))

    return render_template("edit_product.html", product=product)

@app.route("/admin/delete/<int:product_id>", methods=["POST"])
@login_required
def delete_product(product_id):
    global products
    products = [p for p in products if p["id"] != product_id]
    return redirect(url_for("admin_dashboard"))



@app.route("/admin/carousel", methods=["GET", "POST"])
@login_required
def admin_carousel():
    return render_template("admin_carousel.html", admin_name=session.get("admin_name"), carousel_items=carousel_items)

@app.route("/admin/add_carousel_item", methods=["GET", "POST"])
@login_required
def add_carousel_item():
    if request.method == "POST":
        file = request.files.get("img_file")
        title = request.form.get("title")
        desc = request.form.get("desc")
        text_position = request.form.get("text_position") or "center"
        button_text = request.form.get("button_text") or ""
        button_link = request.form.get("button_link") or "#"

        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config["UPLOAD_FOLDER"], filename))

            new_id = max([c["id"] for c in carousel_items]) + 1 if carousel_items else 1
            carousel_items.append({
                "id": new_id,
                "img": filename,
                "title": title,
                "desc": desc,
                "text_position": text_position,
                "button_text": button_text,
                "button_link": button_link
            })

            return redirect(url_for("admin_carousel"))

    return render_template("add_carousel_item.html")


@app.route("/admin/carousel/edit/<int:item_id>", methods=["GET", "POST"])
@login_required
def edit_carousel(item_id):
    item = next((c for c in carousel_items if c["id"] == item_id), None)
    if not item:
        abort(404)

    if request.method == "POST":
        # Завантаження нового зображення
        file = request.files.get("img_file")
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config["UPLOAD_FOLDER"], filename))
            item["img"] = filename

        # Текстові поля
        item["title"] = request.form.get("title") or item["title"]
        item["desc"] = request.form.get("desc") or item["desc"]
        item["text_position"] = request.form.get("text_position") or item["text_position"]
        item["button_text"] = request.form.get("button_text") or item["button_text"]
        item["button_link"] = request.form.get("button_link") or item["button_link"]

        return redirect(url_for("admin_carousel"))

    return render_template("edit_carousel.html", item=item)


# Видалення слайду каруселі
@app.route("/admin/carousel/delete/<int:item_id>", methods=["POST"])
@login_required
def delete_carousel_item(item_id):
    global carousel_items
    item = next((c for c in carousel_items if c["id"] == item_id), None)
    if not item:
        abort(404)
    # Видаляємо елемент зі списку
    carousel_items = [c for c in carousel_items if c["id"] != item_id]
    return redirect(url_for("admin_carousel"))


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("admin"))

# -------------------- Run -------------------- #
if __name__ == "__main__":
    with app.app_context():
        db.create_all()
        db.session.commit()
    app.run(debug=True, port=8001)
