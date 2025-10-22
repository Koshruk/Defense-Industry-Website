from wtforms import Form, BooleanField, StringField, PasswordField, validators, FileField, DateField, SelectField, ValidationError
from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed, FileRequired
from datetime import date

def DateValidation(form, field):
    if field.data and field.data >= date.today():
        raise ValidationError("Date must be before today.")

images = ['jpg', 'png', 'jpeg']

class ProductForm(FlaskForm):
    name = StringField('Назва', [validators.Length(min=4, max=25), validators.DataRequired()])
    description = StringField('Опис', [validators.Length(min=4, max=100), validators.DataRequired()])
    img = FileField('Картинка', validators=[FileRequired(), FileAllowed(images, 'Images only!')])

class UserForm(FlaskForm):
    email = StringField('Email', [validators.Length(min=4, max=80), validators.DataRequired()])
    password = PasswordField('Пароль', [validators.Length(min=4, max=80), validators.DataRequired()])
    name = StringField("Ім'я", [validators.Length(max=20)])

class CarouselItemForm(FlaskForm):
    title = StringField('Слайд', [validators.Length(min=4, max=25), validators.DataRequired()])
    description = StringField('Опис', [validators.Length(min=4, max=50)])
    text_position = SelectField(
        "Розміщення тексту",
        choices=[
            ("left","Зліва"),
            ("center","По центру"),
            ("right","Справа")
        ],
        default="center"
    )
    button_text = StringField('Текст на кнопці', [validators.Length(min=4, max=30), validators.DataRequired()])
    button_link = StringField('Посилання', [validators.Length(min=4, max=50), validators.DataRequired()])
    img = FileField('Картинка', validators=[FileRequired(), FileAllowed(images, 'Тільки зображення!')])