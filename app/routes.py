from flask import render_template, redirect, url_for, flash, request, make_response, current_app, send_from_directory, session, abort
from app import app, db
from app.forms import RegistrationForm, LoginForm, UploadForm
from app.models import User, Dataset
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from werkzeug.utils import secure_filename
from app.utils import validate_json_schema  # надо дописать
from passlib.hash import sha256_crypt
from datetime import datetime
import random, requests, json, os, openai
import re

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

def save_mock_data(mock_data):
    """Безопасное сохранение mock-данных"""
    try:
        # Генерируем безопасное имя файла
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        safe_filename = secure_filename(f"mock_{timestamp}.json")
        
        upload_folder = current_app.config['UPLOAD_FOLDER']
        os.makedirs(upload_folder, exist_ok=True)
        
        file_path = os.path.join(upload_folder, safe_filename)
        
        # Проверка безопасности пути
        if not os.path.abspath(file_path).startswith(os.path.abspath(upload_folder)):
            raise ValueError("Недопустимый путь к файлу")
        
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(mock_data)
        
        dataset = Dataset(
            filename=safe_filename,
            user_id=current_user.id,
            upload_date=datetime.utcnow()
        )
        db.session.add(dataset)
        db.session.commit()
        
        return safe_filename
        
    except Exception as e:
        current_app.logger.error(f"Save error: {str(e)}")
        raise

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

# @app.route('/dashboard')
# @login_required
# def dashboard():
#     datasets = Dataset.query.filter_by(user_id=current_user.id).all()
#     return render_template('dashboard.html', datasets=datasets)

@app.route('/dashboard')
@login_required
def dashboard():
    """Личный кабинет с файлами из БД и физическими файлами"""
    # Получаем файлы из базы данных
    db_datasets = Dataset.query.filter_by(user_id=current_user.id).all()
    
    # Получаем физические файлы из папки uploads
    upload_dir = current_app.config['UPLOAD_FOLDER']
    physical_files = []
    
    if os.path.exists(upload_dir):
        # Фильтруем только файлы текущего пользователя
        user_files = []
        for filename in os.listdir(upload_dir):
            if filename.startswith(f"user_{current_user.id}_"):
                filepath = os.path.join(upload_dir, filename)
                if os.path.isfile(filepath):
                    upload_date = datetime.fromtimestamp(os.path.getmtime(filepath))
                    user_files.append({
                        'filename': filename,
                        'upload_date': upload_date,
                        'is_physical': True  # Флаг, что это физический файл
                    })
        
        physical_files = sorted(user_files, key=lambda x: x['upload_date'], reverse=True)
    
    return render_template('dashboard.html', 
                         db_datasets=db_datasets,
                         physical_files=physical_files)

@app.route('/delete_physical_file', methods=['POST'])
@login_required
def delete_physical_file():
    """Удаление физического файла"""
    try:
        filename = request.form.get('filename')
        if not filename:
            flash('Не указано имя файла', 'danger')
            return redirect(url_for('dashboard'))
            
        safe_filename = secure_filename(filename)
        if not safe_filename:
            raise ValueError("Недопустимое имя файла")
            
        filepath = os.path.join(current_app.config['UPLOAD_FOLDER'], safe_filename)
        
        # Проверка безопасности пути
        if not os.path.abspath(filepath).startswith(os.path.abspath(current_app.config['UPLOAD_FOLDER'])):
            raise ValueError("Попытка доступа к недопустимому пути")
        
        # Проверка существования файла
        if not os.path.exists(filepath):
            flash('Файл не найден', 'warning')
            return redirect(url_for('dashboard'))
        
        # Удаляем файл
        os.remove(filepath)
        flash('Файл успешно удален', 'success')
        
    except Exception as e:
        current_app.logger.error(f"Ошибка при удалении файла: {str(e)}")
        flash('Произошла ошибка при удалении файла', 'danger')
    
    return redirect(url_for('dashboard'))

@app.route('/check_files')
@login_required
def check_files():
    """Страница для отладки - проверка файлов"""
    files = []
    upload_dir = current_app.config['UPLOAD_FOLDER']
    
    # Физические файлы
    if os.path.exists(upload_dir):
        files.extend(os.listdir(upload_dir))
    
    # Файлы в БД
    db_files = Dataset.query.filter_by(user_id=current_user.id).all()
    
    return render_template('check_files.html',
                         physical_files=files,
                         db_files=[f.filename for f in db_files])

# @app.route('/download/<filename>')
# @login_required
# def download_file(filename):
#     """Безопасное скачивание файла"""
#     try:
#         safe_filename = secure_filename(filename)
#         if not safe_filename:
#             raise ValueError("Недопустимое имя файла")
            
#         upload_folder = current_app.config['UPLOAD_FOLDER']
#         file_path = os.path.join(upload_folder, safe_filename)
        
#         # Дополнительная проверка безопасности пути
#         if not os.path.abspath(file_path).startswith(os.path.abspath(upload_folder)):
#             raise ValueError("Попытка доступа к недопустимому пути")
        
#         # Проверка существования файла
#         if not os.path.exists(file_path):
#             current_app.logger.error(f"File not found: {file_path}")
#             abort(404, description="Файл не найден")
        
#         # Проверка принадлежности файла пользователю
#         dataset = Dataset.query.filter_by(filename=safe_filename, user_id=current_user.id).first()
#         if not dataset:
#             abort(403, description="Доступ запрещен")
        
#         return send_from_directory(
#             upload_folder,
#             safe_filename,
#             as_attachment=True,
#             mimetype='application/json'
#         )
        
#     except Exception as e:
#         current_app.logger.error(f"Download error: {str(e)}")
#         abort(500, description=str(e))

@app.route('/download/<filename>')
@login_required
def download_file(filename):
    """Безопасное скачивание файла (из БД или физического)"""
    try:
        safe_filename = secure_filename(filename)
        if not safe_filename:
            raise ValueError("Недопустимое имя файла")
            
        upload_folder = current_app.config['UPLOAD_FOLDER']
        file_path = os.path.join(upload_folder, safe_filename)
        
        # Проверка безопасности пути
        if not os.path.abspath(file_path).startswith(os.path.abspath(upload_folder)):
            raise ValueError("Попытка доступа к недопустимому пути")
        
        # Проверка существования файла
        if not os.path.exists(file_path):
            current_app.logger.error(f"File not found: {file_path}")
            abort(404, description="Файл не найден")
        
        # Для файлов из БД проверяем принадлежность
        if not filename.startswith(f"user_{current_user.id}_"):
            dataset = Dataset.query.filter_by(filename=safe_filename, user_id=current_user.id).first()
            if not dataset:
                abort(403, description="Доступ запрещен")
        
        return send_from_directory(
            upload_folder,
            safe_filename,
            as_attachment=True,
            mimetype='application/json'
        )
        
    except Exception as e:
        current_app.logger.error(f"Download error: {str(e)}")
        abort(500, description=str(e))

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
            #is_valid = validate_json_schema(data, json_schema)

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

@app.route('/mock_result')
@login_required
def mock_result():
    """Страница с результатами генерации"""
    mock_data = request.args.get('data')
    if not mock_data:
        flash('Нет данных для отображения', 'warning')
        return redirect(url_for('mock_generator'))
    
    # Сохраняем данные в сессии для скачивания
    session['last_mock_data'] = mock_data
    return render_template('mock_result.html', mock_data=mock_data)

@app.route('/download_mock')
@login_required
def download_mock():
    """Скачивание последних сгенерированных данных"""
    if 'last_mock_data' not in session:
        flash('Нет данных для скачивания', 'warning')
        return redirect(url_for('mock_generator'))
    
    try:
        # Создаем временный файл
        filename = f"mock_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        filepath = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(session['last_mock_data'])
        
        # Сохраняем запись в БД
        dataset = Dataset(filename=filename, user_id=current_user.id)
        db.session.add(dataset)
        db.session.commit()
        
        return send_from_directory(
            current_app.config['UPLOAD_FOLDER'],
            filename,
            as_attachment=True,
            mimetype='application/json'
        )
    except Exception as e:
        current_app.logger.error(f"Download mock error: {str(e)}")
        flash('Ошибка при создании файла', 'danger')
        return redirect(url_for('mock_result'))
    
@app.route('/delete/<int:file_id>', methods=['POST'])
@login_required
def delete_file(file_id):
    """Удаление файла"""
    try:
        # Находим файл в базе данных
        dataset = Dataset.query.get_or_404(file_id)
        
        # Проверяем, что файл принадлежит текущему пользователю
        if dataset.user_id != current_user.id:
            flash('У вас нет прав для удаления этого файла', 'danger')
            return redirect(url_for('dashboard'))
        
        # Удаляем файл с сервера
        filepath = os.path.join(current_app.config['UPLOAD_FOLDER'], dataset.filename)
        if os.path.exists(filepath):
            os.remove(filepath)
        
        # Удаляем запись из базы данных
        db.session.delete(dataset)
        db.session.commit()
        
        flash('Файл успешно удален', 'success')
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Ошибка при удалении файла: {str(e)}")
        flash('Произошла ошибка при удалении файла', 'danger')
    
    return redirect(url_for('dashboard'))

@app.route('/mock_generator', methods=['GET', 'POST'])
@login_required
def mock_generator():
    if request.method == 'POST':
        try:
            data = request.get_json()
            if not data or 'fields' not in data:
                return {"error": "Invalid request data"}, 400

            count = max(1, min(int(data.get('count', 1)), 100))  # Лимит 100 объектов
            fields = data['fields']

            prompt = f"""
            You MUST generate EXACTLY {count} JSON objects with this structure:
            {json.dumps(fields, indent=2)}

            RULES:
            1. Output MUST be ONLY a JSON array
            2. Use exactly these field names and types
            3. Example valid response:
            [{{"{fields[0]['fieldName']}": "example_value"}}]

            IMPORTANT: DO NOT include any text outside the JSON array!
            """

            response = requests.post(
                "https://openrouter.ai/api/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {current_app.config['OPENROUTER_API_KEY']}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": "mistralai/mistral-7b-instruct",
                    "messages": [{"role": "user", "content": prompt}],
                    "response_format": {"type": "json_object"},
                    "max_tokens": 2000,
                    "temperature": 0.7
                },
                timeout=30
            )

            response.raise_for_status()
            response_data = response.json()
            
            content = response_data['choices'][0]['message']['content']
            
            json_str = re.sub(r'^.*?(\[.*\]).*?$', r'\1', content, flags=re.DOTALL)
            
            try:
                mock_data = json.loads(json_str)
                if not isinstance(mock_data, list):
                    mock_data = [mock_data]
            except json.JSONDecodeError:
                raise ValueError(f"Не удалось распарсить JSON из ответа: {content[:200]}")

            filename = f"mock_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            filepath = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
            
            os.makedirs(os.path.dirname(filepath), exist_ok=True)
            
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(mock_data, f, ensure_ascii=False, indent=2)
            
            # Дополнительная проверка записи
            with open(filepath, 'r', encoding='utf-8') as f:
                saved_data = json.load(f)
                if saved_data != mock_data:
                    raise ValueError("Данные не совпадают после сохранения")

            return {
                "success": True,
                "filename": filename,
                "data": mock_data[:2]
            }

        except requests.exceptions.RequestException as e:
            current_app.logger.error(f"API request failed: {str(e)}")
            return {"error": "Ошибка соединения с API"}, 502
            
        except json.JSONDecodeError as e:
            current_app.logger.error(f"JSON decode error: {str(e)}\nContent: {content[:500]}")
            return {"error": "Ошибка формата данных от API"}, 502
            
        except Exception as e:
            current_app.logger.error(f"Unexpected error: {str(e)}", exc_info=True)
            return {"error": "Внутренняя ошибка сервера"}, 500
    return render_template('mock_generator.html')

# Функции генерации для fallback (если API недоступно)
def generate_string(constraints):
    """Генерация строки с учетом ограничений"""
    if constraints.get('enum'):
        return random.choice([x.strip() for x in constraints['enum'].split(',')])
    
    length = random.randint(
        int(constraints.get('minLength', 5)),
        int(constraints.get('maxLength', 10))
    )
    return ''.join(random.choices('abcdefghijklmnopqrstuvwxyz', k=length))

def generate_number(constraints):
    """Генерация числа с учетом ограничений"""
    if constraints.get('enum'):
        return float(random.choice([x.strip() for x in constraints['enum'].split(',')]))
    
    return round(random.uniform(
        float(constraints.get('minimum', 0)),
        float(constraints.get('maximum', 100))), 
        2
    )

def generate_array(constraints):
    """Генерация массива с учетом ограничений"""
    size = random.randint(1, 5)
    item_type = constraints.get('items', {}).get('type', 'string')
    
    if item_type == 'string':
        return [generate_string({}) for _ in range(size)]
    elif item_type == 'number':
        return [generate_number({}) for _ in range(size)]
    return []