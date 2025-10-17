from flask import Flask, render_template, request, redirect, url_for, abort, session, flash
from werkzeug.utils import secure_filename
from functools import wraps
from flask_migrate import Migrate
from flask_login import login_user, LoginManager, login_required, logout_user, current_user
from sqlalchemy import or_
from flask_bcrypt import Bcrypt
import os
import uuid

from models import db, Product, Admin, CarouselItem
from forms import ProductForm, AdminForm, CarouselItemForm

app = Flask(__name__)
app.secret_key = "SayGex"

UPLOAD_FOLDER = "static/img"
ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "gif"}

app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///products_database.db"
app.config['MAX_CONTENT_LENGTH'] = 5 * 1024 * 1024

db.init_app(app)
bcrypt = Bcrypt(app)
migrate = Migrate(app, db)

login_manager = LoginManager()
login_manager.init_app(app)
@login_manager.user_loader
def load_user(user_id):
    return db.session.get(Admin, int(user_id))

def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS



def superadmin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role != "superadmin":
            abort(403)
        return f(*args, **kwargs)
    return decorated_function

# -------------------- Routes -------------------- #

@app.route("/")
def index():
    carousel_items = CarouselItem.query.all()
    return render_template("index.html", carousel_items=carousel_items)

@app.route("/products")
def products_page():
    products = Product.query.all()
    return render_template("products.html", products=products)

@app.route("/products/<int:product_id>")
def product_detail(product_id):
    product = Product.query.get(product_id)
    if not product:
        abort(404)
    return render_template("product_detail.html", product=product)

@app.route("/admin", methods=["GET", "POST"])
def admin():
    form = AdminForm()
    if form.validate_on_submit():
        admin_user = Admin.query.filter_by(email = form.email.data).first()
        if admin_user and bcrypt.check_password_hash(admin_user.password, form.password.data):
            login_user(admin_user)
            return redirect(url_for("admin_dashboard"))
        else:
            flash("Неправильний email та/або пароль", "danger")
            
    return render_template("admin.html", form=form)

@app.route("/admin/dashboard")
@login_required
def admin_dashboard():
    q = request.args.get("q", "").lower()
    filtered_products = Product.query.filter(or_(Product.name.ilike(f"%{q}%")), Product.description.ilike(f"%{q}%")).all()
    return render_template("admin_dashboard.html", products=filtered_products)

@app.route("/admin/admins")
@login_required
def admin_list():
    q = request.args.get("q", "").lower()
    filtered_admins = Admin.query.filter(or_(Admin.name.ilike(f"%{q}%"), Admin.email.ilike(f"%{q}%"))).all()
    return render_template("admin_dashboard_admins.html", admins=filtered_admins)

@app.route("/admin/add_admin", methods=["GET", "POST"])
@superadmin_required
def add_admin():
    form = AdminForm()
    if form.validate_on_submit():
        hashed_password = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
        admin = Admin(name = form.name.data,
                          email = form.email.data,
                          password = hashed_password)
        db.session.add(admin)
        db.session.commit()
        return redirect(url_for("admin_list"))
    return render_template("add_admin.html", form=form)

@app.route("/admin/delete/<int:admin_id>", methods=["POST"])
@superadmin_required
def delete_admin(admin_id):
    admin = Admin.query.get_or_404(admin_id)
    if admin.id == current_user.id:
        flash("You cannot delete your own account", "danger")
        return redirect(url_for("admin_list"))
    db.session.delete(admin)
    db.session.commit()
    return redirect(url_for("admin_list"))

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
    current_product = Product.query.get_or_404(product_id)
    form = ProductForm(obj=current_product)

    if form.validate_on_submit():
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
    
    return render_template("edit_product.html", product=current_product, form=form)

@app.route("/admin/delete/<int:product_id>", methods=["POST"])
@login_required
def delete_product(product_id):
    product = Product.query.get_or_404(product_id)
    if product.img:
        img_path = os.path.join(UPLOAD_FOLDER, product.img)
        if os.path.exists(img_path):
            os.remove(img_path)
    db.session.delete(product)
    db.session.commit()
    return redirect(url_for("admin_dashboard"))



@app.route("/admin/carousel", methods=["GET", "POST"])
@login_required
def admin_carousel():
    carousel_items = CarouselItem.query.all()
    return render_template("admin_carousel.html", carousel_items=carousel_items)

@app.route("/admin/add_carousel_item", methods=["GET", "POST"])
@login_required
def add_carousel_item():
    form = CarouselItemForm()
    if form.validate_on_submit():
        carousel_item = CarouselItem(title = form.title.data,
                          description = form.description.data,
                          text_position = form.text_position.data,
                          button_text = form.button_text.data,
                          button_link = form.button_link.data,
                          img = form.img.data)
        if form.img.data:
            filename = f"{uuid.uuid4().hex}_{secure_filename(form.img.data.filename)}"
            upload_path = os.path.join(UPLOAD_FOLDER, filename)
            form.img.data.save(upload_path)
            carousel_item.img = filename
        db.session.add(carousel_item)
        db.session.commit()
        return redirect(url_for("admin_carousel"))

    return render_template("add_carousel_item.html", form = form)


@app.route("/admin/carousel/edit/<int:item_id>", methods=["GET", "POST"])
@login_required
def edit_carousel(item_id):
    current_carousel_item = CarouselItem.query.get_or_404(item_id)
    form = CarouselItemForm(obj=current_carousel_item)
    if form.validate_on_submit():
        current_carousel_item.title = form.title.data
        current_carousel_item.description = form.description.data
        current_carousel_item.text_position = form.text_position.data
        current_carousel_item.button_text = form.button_text.data
        current_carousel_item.button_link = form.button_link.data
        if form.img.data:
            if current_carousel_item.img:
                img_path = os.path.join(UPLOAD_FOLDER, current_carousel_item.img)
                if os.path.exists(img_path):
                    os.remove(img_path)
            filename = secure_filename(form.img.data.filename)
            upload_path = os.path.join(UPLOAD_FOLDER, filename)
            form.img.data.save(upload_path)
            current_carousel_item.img = filename

        db.session.commit()
        return redirect(url_for("admin_carousel"))

    return render_template("edit_carousel.html", carousel_item=current_carousel_item, form=form)


@app.route("/admin/carousel/delete/<int:item_id>", methods=["POST"])
@login_required
def delete_carousel_item(item_id):
    carousel_item = CarouselItem.query.get_or_404(item_id)
    if carousel_item.img:
        img_path = os.path.join(UPLOAD_FOLDER, carousel_item.img)
        if os.path.exists(img_path):
            os.remove(img_path)
    db.session.delete(carousel_item)
    db.session.commit()
    return redirect(url_for("admin_carousel"))


@app.route("/logout")
def logout():
    logout_user()
    return redirect(url_for("admin"))

# -------------------- Run -------------------- #
if __name__ == "__main__":
    with app.app_context():
        db.create_all()
        db.session.commit()
    app.run(debug=True, port=8001)
