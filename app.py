from flask import Flask, render_template, request, redirect, url_for, abort, session, flash
from functools import wraps
from werkzeug.utils import secure_filename
from flask_migrate import Migrate
from flask_login import login_user, LoginManager, login_required, logout_user
import os
import uuid

from models import db, Product, Admin
from forms import ProductForm, AdminForm

app = Flask(__name__)
app.secret_key = "SayGex"  # Для сесій

UPLOAD_FOLDER = "static/img"  # де будуть зберігатися завантажені файли
ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "gif"}
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///products_database.db"
app.config['MAX_CONTENT_LENGTH'] = 5 * 1024 * 1024
db.init_app(app)
migrate = Migrate(app, db)
login_manager = LoginManager()
login_manager.init_app(app)
@login_manager.user_loader
def load_user(user_id):
    return db.session.get(Admin, int(user_id))

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
    form = AdminForm()
    admins = Admin.query.all()
    if form.validate_on_submit():
        admin_user = next((a for a in admins if a.email == form.email.data and a.password == form.password.data), None)
        if admin_user:
            print("user")
            login_user(admin_user)
            return redirect(url_for("admin_dashboard"))
        else:
            flash('Wrong email or password')
    return render_template("admin.html", form=form)

@app.route("/admin/dashboard")
@login_required
def admin_dashboard():
    q = request.args.get("q", "").lower()
    products = Product.query.all()
    filtered_products = [p for p in products if q in p.name.lower()] if q else products
    return render_template("admin_dashboard.html", products=filtered_products)

@app.route("/admin/admins")
@login_required
def admin_list():
    q = request.args.get("q", "").lower()
    admins = Admin.query.all()
    filtered_admins = [p for p in admins if q in p.name.lower()] if q else admins
    return render_template("admin_dashboard_admins.html", admins=filtered_admins)

@app.route("/admin/add_product", methods=["GET", "POST"])
@login_required
def add_product():
    form = ProductForm()
    if form.validate_on_submit():
        product = Product(name = form.name.data,
                          description = form.description.data,
                          img = form.img.data)
        if form.img.data:
            filename = f"{uuid.uuid4().hex}_{secure_filename(form.img.data.filename)}"
            upload_path = os.path.join(UPLOAD_FOLDER, filename)
            form.img.data.save(upload_path)
            product.img = filename
        db.session.add(product)
        db.session.commit()
        return redirect(url_for("admin_dashboard"))

    return render_template("add_product.html", form = form)

@app.route("/admin/edit/<int:product_id>", methods=["GET", "POST"])
@login_required
def edit_product(product_id):
    products = Product.query.all()
    form = ProductForm()
    product = next((p for p in products if p.id == product_id), None)
    if not product:
        abort(404)

    if request.method == "POST":
        product = Product(name = form.name.data,
                          description = form.description.data,
                          img = form.img.data)
        
        current_product = Product.query.get(product_id)
        if current_product:
            current_product.name = form.name.data
            current_product.description = form.description.data
            if form.img.data:
                if current_product.img:
                    img_path = os.path.join(UPLOAD_FOLDER, current_product.img)
                    if os.path.exists(img_path):
                        os.remove(img_path)
                filename = secure_filename(form.img.data.filename)
                upload_path = os.path.join(UPLOAD_FOLDER, filename)
                form.img.data.save(upload_path)
                current_product.img = filename

        db.session.commit()
        return redirect(url_for("admin_dashboard"))

    return render_template("edit_product.html", product=product, form=form)

@app.route("/admin/delete/<int:product_id>", methods=["POST"])
@login_required
def delete_product(product_id):
    product = Product.query.get(product_id)
    if product:
        if product.img:
            img_path = os.path.join(UPLOAD_FOLDER, product.img)
            if os.path.exists(img_path):
                os.remove(img_path)
        db.session.delete(product)
        db.session.commit()
        return redirect(url_for("admin_dashboard"))
    flash('Product not found', 'error')
    return redirect(url_for("admin_dashboard"))



@app.route("/admin/carousel", methods=["GET", "POST"])
@login_required
def admin_carousel():
    return render_template("admin_carousel.html", carousel_items=carousel_items)

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
