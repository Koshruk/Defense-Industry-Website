from flask import Blueprint, render_template, abort
from extentions import rbac
from flask_login import current_user, logout_user

public_bp = Blueprint('public', __name__,
                        template_folder='templates')

@public_bp.route('/')
def index():
    logout_user()
    return "WOW"