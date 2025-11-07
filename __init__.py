from flask import Flask
from extentions import db, bcrypt, migrate, login_manager, rbac
import os
from flask_login import login_required, logout_user
from flask_login import current_user


def create_app():
    app = Flask(__name__)
    app.secret_key = "SayGex"

    BASE_DIR = os.path.abspath(os.path.dirname(__file__))

    # Configuration
    app.config["UPLOAD_FOLDER"] = "static/img"
    app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{os.path.join(BASE_DIR, 'instance/products_database.db')}"
    app.config["MAX_CONTENT_LENGTH"] = 5 * 1024 * 1024
    app.config["RBAC_USE_WHITE"] = True

    # Initialize extensions
    db.init_app(app)
    bcrypt.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)

    # Configure Login Manager
    @login_manager.user_loader
    def load_user(user_id):
        return db.session.get(User, int(user_id))
        
    with app.app_context():
        db.create_all()

    
    from models import Role, User
    rbac.init_app(app)
    rbac.set_role_model(Role)
    rbac.set_user_model(User)
    rbac._fetch_user = lambda: current_user

    rbac.allow(['anonymous'], ['GET'], '/')

    from blueprints.public.public import public_bp
    app.register_blueprint(public_bp)

    
    return app