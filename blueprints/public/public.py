from flask import Blueprint, render_template, abort
from extentions import rbac
from flask_login import current_user, logout_user, login_user
from models import User

public_bp = Blueprint('public', __name__,
                        template_folder='templates')

@public_bp.route('/')
@rbac.allow(['anonymous', 'admin'], ['GET'], endpoint='public.index')
def index():
    return "test page"