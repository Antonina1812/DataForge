from flask_wtf import FlaskForm
from flask_wtf.file import FileAllowed
from flask import current_app
from wtforms import StringField, PasswordField, SubmitField, FileField
from wtforms.validators import DataRequired, EqualTo, Length
from wtforms import ValidationError
from app.models import User
from app import app

class RegistrationForm(FlaskForm):
    username = StringField('Имя пользователя', validators=[DataRequired(), Length(min=4, max=80)])
    password = PasswordField('Пароль', validators=[DataRequired(), Length(min=6)])
    confirm_password = PasswordField('Подтвердите пароль', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Зарегистрироваться')

    def validate_username(self, username):
        user = User.query.filter_by(username=username.data).first()
        if user:
            raise ValidationError('Это имя пользователя уже занято.')


class LoginForm(FlaskForm):
    username = StringField('Имя пользователя', validators=[DataRequired()]) # логинимся по юзернейму
    password = PasswordField('Пароль', validators=[DataRequired()])
    submit = SubmitField('Войти')


class UploadForm(FlaskForm):
    with app.app_context():
        data_file = FileField(
            'Выберите файл',
            validators=[
                DataRequired(),
                FileAllowed(
                    current_app.config['ALLOWED_EXTENSIONS'],
                    'Допустимые форматы: .csv, .xls, .xlsx, .json'
                )
            ]
        )
        submit = SubmitField('Загрузить')