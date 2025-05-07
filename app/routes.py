from flask import render_template, redirect, url_for, flash, request, send_from_directory
from app import app, db
from app.forms import RegistrationForm, LoginForm, UploadForm
from app.models import User, Dataset
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
import os
import json
from werkzeug.utils import secure_filename
from app.utils import validate_json_schema  # надо дописать
from passlib.hash import sha256_crypt

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegistrationForm()
    if form.validate_on_submit():
        hashed_password = sha256_crypt.hash(form.password.data)
        user = User(username=form.username.data, password=hashed_password)
        db.session.add(user)
        db.session.commit()
        flash('Регистрация прошла успешно! Теперь вы можете войти.', 'success')
        return redirect(url_for('login'))
    return render_template('register.html', form=form)

@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user and sha256_crypt.verify(form.password.data,user.password):
            login_user(user)
            flash('Вы успешно вошли!', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('Неверный логин или пароль.', 'danger')
    return render_template('login.html', form=form)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Вы вышли из аккаунта.', 'info')
    return redirect(url_for('index'))

@app.route('/dashboard')
@login_required
def dashboard():
    datasets = Dataset.query.filter_by(user_id=current_user.id).all()
    return render_template('dashboard.html', datasets=datasets)

@app.route('/upload', methods=['GET', 'POST'])
@login_required
def upload():
    form = UploadForm()
    if form.validate_on_submit():
        f = form.data_file.data
        filename = secure_filename(f.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        f.save(filepath)

        # Валидация JSON файла (нужно написать validate_json_schema в utils.py)
        try:
            with open(filepath, 'r') as file:
                data = json.load(file)

            #Здесь можно добавить вызов функции для определения схемы
            #json_schema =  autodetect_json_schema(data)
            #is_valid = validate_json_schema(data, json_schema) # Позже реализуем валидацию

            is_valid = True # пока не пишем валидацию
            if is_valid:
                dataset = Dataset(filename=filename, user_id=current_user.id)
                db.session.add(dataset)
                db.session.commit()
                flash('Файл успешно загружен и сохранен!', 'success')
                return redirect(url_for('dashboard'))
            else:
                os.remove(filepath) # Удаляем невалидный файл
                flash('Ошибка: Невалидный JSON файл.', 'danger')

        except json.JSONDecodeError:
            os.remove(filepath)
            flash('Ошибка: Некорректный JSON формат.', 'danger')
        except Exception as e:
            os.remove(filepath)
            flash(f'Произошла ошибка при обработке файла: {e}', 'danger')


    return render_template('upload.html', form=form)

def validate_json_schema(data, schema):
    pass

def autodetect_json_schema(data):
    pass