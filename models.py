from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import CheckConstraint, event
from flask_login import LoginManager, UserMixin
from flask_bcrypt import Bcrypt
from flask_rbac import RoleMixin
from extentions import db
bcrypt = Bcrypt()

class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)
    description = db.Column(db.String(100), nullable=False)  
    img = db.Column(db.String(50), nullable=True)
    search_tags = db.Column(db.String(200), nullable=True, default="")

users_roles = db.Table(
    'users_roles',
    db.Column('user_id', db.Integer, db.ForeignKey('user.id')),
    db.Column('role_id', db.Integer, db.ForeignKey('role.id'))
)

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    password_hash = db.Column(db.String(128), nullable=True)
    name = db.Column(db.String(50), nullable=True)
    email = db.Column(db.String(50), nullable=False)
    search_tags = db.Column(db.String(200), nullable=True, default="")
    
    roles = db.relationship(
        'Role',
        secondary=users_roles,
        backref=db.backref('users', lazy='dynamic'),
        lazy='select'
    )

    def add_role(self, role):
        self.roles.append(role)

    def add_roles(self, roles):
        for role in roles:
            self.add_role(role)

    def get_roles(self):
        return self.roles
    
    def has_role(self, role_name):
        return any(role.name == role_name for role in self.roles)

    @property
    def password(self):
        raise AttributeError("Password is write-only!")
    @password.setter
    def password(self, plaintext_password):
        self.password_hash = bcrypt.generate_password_hash(plaintext_password).decode('utf-8')
    
    def check_password(self, plain_password):
        return bcrypt.check_password_hash(self.password_hash, plain_password)

class CarouselItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(25), nullable=True)
    description = db.Column(db.String(50), nullable=True)
    text_position = db.Column(db.String(10), nullable=False, default="center")
    button_text = db.Column(db.String(30), nullable=True)
    button_link = db.Column(db.String(50), nullable=True)
    img = db.Column(db.String(50), nullable=True) 
    search_tags = db.Column(db.String(200), nullable=True, default="")
    __table_args__ = (
        CheckConstraint("text_position IN ('center', 'left', 'right')"),
    )

roles_parents = db.Table(
    'roles_parents',
    db.Column('role_id', db.Integer, db.ForeignKey('role.id')),
    db.Column('parent_id', db.Integer, db.ForeignKey('role.id'))
)

class Role(db.Model, RoleMixin):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(20))
    parents = db.relationship(
        'Role',
        secondary=roles_parents,
        primaryjoin=(id == roles_parents.c.role_id),
        secondaryjoin=(id == roles_parents.c.parent_id),
        backref=db.backref('children', lazy='dynamic')
    )

    def __init__(self, name):
        RoleMixin.__init__(self)
        self.name = name

    def add_parent(self, parent):
        # You don't need to add this role to parent's children set,
        # relationship between roles would do this work automatically
        self.parents.append(parent)

    def add_parents(self, *parents):
        print("Added parent")
        for parent in parents:
            self.add_parent(parent)

    @staticmethod
    def get_by_name(name):
        return Role.query.filter_by(name=name).first()


@event.listens_for(Product, "before_insert")
@event.listens_for(Product, "before_update")
@event.listens_for(User, "before_insert")
@event.listens_for(User, "before_update")
@event.listens_for(CarouselItem, "before_insert")
@event.listens_for(CarouselItem, "before_update")
def update_search_tags(mapper, connection, target):
    parts = []

    for attr in ("name", "description", "title", "role", "email"):
        value = getattr(target, attr, None)
        if value:
            parts.append(str(value))

    combined = " ".join(parts).lower().strip()
    target.search_tags = combined

