from wtforms import Form, BooleanField, StringField, PasswordField, validators, FileField, DateField, ValidationError
from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed, FileRequired
from datetime import date

def DateValidation(form, field):
    if field.data and field.data >= date.today():
        raise ValidationError("Date must be before today.")

images = ['jpg', 'png', 'jpeg']

class ProductForm(FlaskForm):
    name = StringField('Product name', [validators.Length(min=4, max=25), validators.DataRequired()])
    description = StringField('Description', [validators.Length(min=4, max=100), validators.DataRequired()])
    img = FileField('Product picture', validators=[FileRequired(), FileAllowed(images, 'Images only!')])

class AdminForm(FlaskForm):
    email = StringField('Email', [validators.Length(min=4, max=80), validators.DataRequired()])
    password = StringField('Password', [validators.Length(min=4, max=80), validators.DataRequired()])