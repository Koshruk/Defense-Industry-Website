from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import CheckConstraint
from flask_login import LoginManager, UserMixin
db = SQLAlchemy()

class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), nullable=False)
    description = db.Column(db.String(200), nullable=False)  
    img = db.Column(db.String(50), nullable=True) 

class Admin(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    password = db.Column(db.String(80), nullable=False)
    name = db.Column(db.String(80), nullable=True)
    email = db.Column(db.String(80), nullable=False)

class CarouselItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(25), nullable=True)
    description = db.Column(db.String(50), nullable=True)
    text_position = db.Column(db.String(10), nullable=False, default="center")
    button_text = db.Column(db.String(30), nullable=True)
    button_link = db.Column(db.String(50), nullable=True)
    img = db.Column(db.String(50), nullable=True) 
    __table_args__ = (
        CheckConstraint("text_position IN ('center', 'left', 'right')"),
    )

