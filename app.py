from flask import Flask, render_template, request, redirect, url_for, abort, session, flash, jsonify
from werkzeug.utils import secure_filename
from functools import wraps
from flask_migrate import Migrate
from flask_login import login_user, LoginManager, login_required, logout_user, current_user
from sqlalchemy import or_
from flask_bcrypt import Bcrypt
from flask_rbac import RBAC
import os
import uuid

from models import db, Product, User, CarouselItem, Role
from forms import ProductForm, UserForm, CarouselItemForm

app = Flask(__name__)
app.secret_key = "SayGex"

UPLOAD_FOLDER = "static/img"
ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "gif"}

app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///products_database.db"
app.config['MAX_CONTENT_LENGTH'] = 5 * 1024 * 1024
app.config['RBAC_USE_WHITE'] = True

db.init_app(app)
bcrypt = Bcrypt(app)
migrate = Migrate(app, db)

login_manager = LoginManager()
login_manager.init_app(app)
@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))


rbac = RBAC(app)
rbac.set_role_model(Role)
rbac.set_user_model(User)

def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS

# -------------------- Routes -------------------- #

@app.route("/")
@rbac.allow(["anonymous"], methods=["GET"])
def index():
    carousel_items = CarouselItem.query.all()
    return render_template("index.html", carousel_items=carousel_items)

@app.route("/role")
@rbac.allow(["anonymous", 'admin'], methods=["GET"])
def role():
    if not current_user.is_authenticated:
        return jsonify({
            "authenticated": False,
            "roles": getattr(current_user, "roles", None)
        })
    else:
        return jsonify({
            "authenticated": True,
            "id": current_user.id,
            "roles": [r.name for r in current_user.roles]
        })

@app.route("/products")
@rbac.allow(["anonymous"], methods=["GET"])
def products_page():
    products = Product.query.all()
    return render_template("products.html", products=products)

@app.route("/products/<int:product_id>")
@rbac.allow(["anonymous"], methods=["GET"])
def product_detail(product_id):
    product = Product.query.get_or_404(product_id)
    return render_template("product_detail.html", product=product)

@app.route("/admin", methods=["GET", "POST"])
@rbac.allow(["anonymous", "admin"], methods=["GET", "POST"])
def admin():
    form = UserForm()
    if form.validate_on_submit():
        admin_user = User.query.filter_by(email = form.email.data).first()
        if admin_user and admin_user.check_password(form.password.data):
            login_user(admin_user)
            return redirect(url_for("admin_dashboard"))
        else:
            flash("Неправильний email та/або пароль", "danger")
            
    return render_template("admin.html", form=form)

@app.route("/admin/dashboard")
@login_required
@rbac.allow(["admin"], methods=["GET"])
def admin_dashboard():
    q = request.args.get("q", "").lower()
    page = db.paginate(Product.query.filter(Product.search_tags.ilike(f"%{q}%")), per_page=5)
    return render_template("admin_dashboard.html", page=page)

@app.route("/admin/admins")
@login_required
@rbac.allow(["admin"], methods=["GET"])
def admin_list():
    q = request.args.get("q", "").lower()
    page = db.paginate(User.query.filter(User.search_tags.ilike(f"%{q}%")), per_page=5)
    return render_template("admin_dashboard_admins.html", page=page)

@app.route("/admin/add_admin", methods=["GET", "POST"])
@login_required
@rbac.allow(["superadmin"], methods=["GET", "POST"])
def add_admin():
    form = UserForm()
    if form.validate_on_submit():
        admin = User()
        form.populate_obj(admin)
        db.session.add(admin)
        db.session.commit()
        return redirect(url_for("admin_list"))
    return render_template("add_admin.html", form=form)

@app.route("/admin/admins/edit/<int:admin_id>", methods=["GET", "POST"])
@login_required
@rbac.allow(["superadmin"], methods=["GET", "POST"])
def edit_admin(admin_id):
    current_admin = User.query.get_or_404(admin_id)
    form = UserForm()
    if form.validate_on_submit():
        form.populate_obj(current_admin)
        db.session.commit()
        return redirect(url_for("admin_list"))
    return render_template("edit_admin.html", form=form)

@app.route("/admin/admins/delete/<int:admin_id>", methods=["POST"])
@login_required
@rbac.allow(["superadmin"], methods=["POST"])
def delete_admin(admin_id):
    admin = User.query.get_or_404(admin_id)
    if admin.id == current_user.id:
        flash("You cannot delete your own account", "danger")
        return redirect(url_for("admin_list"))
    db.session.delete(admin)
    db.session.commit()
    return redirect(url_for("admin_list"))

@app.route("/admin/add_product", methods=["GET", "POST"])
@login_required
@rbac.allow(["admin"], methods=["GET", "POST"])
def add_product():
    form = ProductForm()
    if form.validate_on_submit():
        if form.img.data:
            filename = f"{uuid.uuid4().hex}_{secure_filename(form.img.data.filename)}"
            upload_path = os.path.join(UPLOAD_FOLDER, filename)
            form.img.data.save(upload_path)
            form.img.data = filename
        product = Product()
        form.populate_obj(product)
        db.session.add(product)
        db.session.commit()
        return redirect(url_for("admin_dashboard"))

    return render_template("add_product.html", form = form)

@app.route("/admin/edit/<int:product_id>", methods=["GET", "POST"])
@login_required
@rbac.allow(["admin"], methods=["GET", "POST"])
def edit_product(product_id):
    current_product = Product.query.get_or_404(product_id)
    form = ProductForm(obj=current_product)

    if form.validate_on_submit():
        if form.img.data:
            if current_product.img:
                img_path = os.path.join(UPLOAD_FOLDER, current_product.img)
                if os.path.exists(img_path):
                    os.remove(img_path)
            filename = secure_filename(form.img.data.filename)
            upload_path = os.path.join(UPLOAD_FOLDER, filename)
            form.img.data.save(upload_path)
            form.img.data = filename
        form.populate_obj(current_product)
        db.session.commit()
        return redirect(url_for("admin_dashboard"))
    
    return render_template("edit_product.html", product=current_product, form=form)

@app.route("/admin/delete/<int:product_id>", methods=["POST"])
@login_required
@rbac.allow(["admin"], methods=["POST"])
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
@rbac.allow(["admin"], methods=["GET", "POST"])
def admin_carousel():
    q = request.args.get("q", "").lower()
    page = db.paginate(CarouselItem.query.filter(CarouselItem.search_tags.ilike(f"%{q}%")), per_page=5)
    return render_template("admin_carousel.html", page=page)

@app.route("/admin/add_carousel_item", methods=["GET", "POST"])
@login_required
@rbac.allow(["admin"], methods=["GET", "POST"])
def add_carousel_item():
    form = CarouselItemForm()
    if form.validate_on_submit():
        if form.img.data:
            filename = f"{uuid.uuid4().hex}_{secure_filename(form.img.data.filename)}"
            upload_path = os.path.join(UPLOAD_FOLDER, filename)
            form.img.data.save(upload_path)
            form.img.data = filename
        carousel_item = CarouselItem()
        form.populate_obj(carousel_item)
        db.session.add(carousel_item)
        db.session.commit()
        return redirect(url_for("admin_carousel"))

    return render_template("add_carousel_item.html", form = form)


@app.route("/admin/carousel/edit/<int:item_id>", methods=["GET", "POST"])
@login_required
@rbac.allow(["admin"], methods=["GET", "POST"])
def edit_carousel(item_id):
    current_carousel_item = CarouselItem.query.get_or_404(item_id)
    form = CarouselItemForm(obj=current_carousel_item)
    if form.validate_on_submit():
        
        if form.img.data:
            if current_carousel_item.img:
                img_path = os.path.join(UPLOAD_FOLDER, current_carousel_item.img)
                if os.path.exists(img_path):
                    os.remove(img_path)
            filename = secure_filename(form.img.data.filename)
            upload_path = os.path.join(UPLOAD_FOLDER, filename)
            form.img.data.save(upload_path)
            form.img.data = filename
        form.populate_obj(current_carousel_item)
        db.session.commit()
        return redirect(url_for("admin_carousel"))

    return render_template("edit_carousel.html", carousel_item=current_carousel_item, form=form)


@app.route("/admin/carousel/delete/<int:item_id>", methods=["POST"])
@login_required
@rbac.allow(["admin"], methods=["POST"])
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
@login_required
@rbac.allow(["admin"], methods=["GET"])
def logout():
    logout_user()
    return redirect(url_for("admin"))

# -------------------- Run -------------------- #
if __name__ == "__main__":
    with app.app_context():
        db.create_all()
        db.session.commit()
    app.run(debug=True, port=8001)
