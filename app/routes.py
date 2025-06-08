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

@app.route('/dashboard')
@login_required
def dashboard():
    datasets = Dataset.query.filter_by(user_id=current_user.id).all()
    return render_template('dashboard.html', datasets=datasets)

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

@app.route('/download/<filename>')
@login_required
def download_file(filename):
    """Безопасное скачивание файла"""
    try:
        safe_filename = secure_filename(filename)
        if not safe_filename:
            raise ValueError("Недопустимое имя файла")
            
        upload_folder = current_app.config['UPLOAD_FOLDER']
        file_path = os.path.join(upload_folder, safe_filename)
        
        # Дополнительная проверка безопасности пути
        if not os.path.abspath(file_path).startswith(os.path.abspath(upload_folder)):
            raise ValueError("Попытка доступа к недопустимому пути")
        
        # Проверка существования файла
        if not os.path.exists(file_path):
            current_app.logger.error(f"File not found: {file_path}")
            abort(404, description="Файл не найден")
        
        # Проверка принадлежности файла пользователю
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

# @app.route('/mock_generator', methods=['GET', 'POST'])
# @login_required
# def mock_generator():
#     if request.method == 'POST':
#         try:
#             data = request.get_json()
#             if not data:
#                 return {"error": "No data provided"}, 400
                
#             count = int(data.get('count', 1))  # По умолчанию 1 объект
#             fields = data.get('fields', [])
            
#             if not isinstance(fields, list):
#                 return {"error": "Fields should be an array"}, 400

#             mock_objects = []
#             for _ in range(count):
#                 mock_object = {}
#                 for field in fields:
#                     if not isinstance(field, dict):
#                         continue
                        
#                     field_name = field.get('fieldName')
#                     if not field_name:
#                         continue
                        
#                     field_type = field.get('fieldType', 'string')
#                     constraints = field.get('constraints', {}) or {}
                    
#                     try:
#                         if field_type == 'string':
#                             mock_object[field_name] = generate_string(constraints)
#                         elif field_type == 'number':
#                             mock_object[field_name] = generate_number(constraints)
#                         elif field_type == 'boolean':
#                             mock_object[field_name] = True
#                         elif field_type == 'array':
#                             mock_object[field_name] = generate_array(constraints)
#                         elif field_type == 'date':
#                             mock_object[field_name] = datetime.now().strftime('%Y-%m-%d')
#                     except Exception as e:
#                         print(f"Error generating field {field_name}: {str(e)}")
#                         mock_object[field_name] = None
                
#                 if mock_object:  # Добавляем только если есть данные
#                     mock_objects.append(mock_object)
            
#             if not mock_objects:
#                 return {"error": "No valid fields to generate"}, 400
            
#             # Сохраняем в базу данных
#             filename = f"mock_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
#             mock_data = json.dumps(mock_objects, ensure_ascii=False, indent=2)
            
#             dataset = Dataset(filename=filename, user_id=current_user.id)
#             db.session.add(dataset)
#             db.session.commit()
            
#             # Сохраняем файл на сервере
#             filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
#             with open(filepath, 'w', encoding='utf-8') as f:
#                 f.write(mock_data)
            
#             return {"success": True, "mockData": mock_data}
        
#         except Exception as e:
#             print(f"Error in mock_generator: {str(e)}")
#             return {"error": str(e)}, 500
    
#     return render_template('mock_generator.html')

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

# def generate_string(constraints):
#     if constraints.get('enum'):
#         enum_values = [v.strip() for v in constraints['enum'].split(',') if v.strip()]
#         if enum_values:
#             return random.choice(enum_values)
    
#     min_len = max(0, int(constraints.get('minLength', 5)))
#     max_len = max(min_len, int(constraints.get('maxLength', 10)))
#     length = random.randint(min_len, max_len)
#     chars = 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789'
#     return ''.join(random.choices(chars, k=length))

# def generate_number(constraints):
#     if constraints.get('enum'):
#         enum_values = [float(v.strip()) for v in constraints['enum'].split(',') if v.strip()]
#         if enum_values:
#             return random.choice(enum_values)
    
#     minimum = float(constraints.get('minimum', 0))
#     maximum = float(constraints.get('maximum', 100))
#     return round(random.uniform(minimum, maximum), 2)

# def generate_array(constraints):
#     items_type = constraints.get('items', {}).get('type', 'string')
#     return [generate_simple_value(items_type) for _ in range(random.randint(1, 5))]

# def generate_simple_value(field_type):
#     if field_type == 'string':
#         return ''.join(random.choices('abcde', k=5))
#     elif field_type == 'number':
#         return random.randint(1, 100)
#     elif field_type == 'boolean':
#         return random.choice([True, False])
#     return None

@app.route('/mock_generator', methods=['GET', 'POST'])
@login_required
def mock_generator():
    if request.method == 'POST':
        try:
            data = request.get_json()
            count = int(data.get('count', 1))
            fields = data.get('fields', [])

            # Настройка клиента OpenAI для OpenRouter
            openai.api_base = "https://openrouter.ai/api/v1"
            openai.api_key = current_app.config['OPENROUTER_API_KEY']
            
            # Формируем промпт для ИИ
            prompt = f"""
            Сгенерируй {count} JSON-объектов со следующими полями:
            {json.dumps(fields, indent=2)}
            
            Требования:
            1. Все поля должны соответствовать указанным типам
            2. Учитывай все constraints
            3. Верни ТОЛЬКО JSON-массив без каких-либо пояснений
            """

            # Отправляем запрос
            response = openai.ChatCompletion.create(
                model="openai/gpt-4o",  # Экономная модель
                messages=[{"role": "user", "content": prompt}],
                max_tokens=4000,  # Явное ограничение
                headers={
                    "HTTP-Referer": request.host_url,
                    "X-Title": "DataForge Mock Generator"
                }
            )
            
            # Извлекаем и валидируем ответ
            generated_content = response.choices[0].message.content
            mock_objects = json.loads(generated_content.strip())

            # Сохранение результатов (как в предыдущем примере)
            filename = f"mock_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            mock_data = json.dumps(mock_objects, ensure_ascii=False, indent=2)
            
            dataset = Dataset(
                filename=filename,
                user_id=current_user.id,
                data_type='json',
                source='openrouter-gpt4'
            )
            db.session.add(dataset)
            db.session.commit()
            
            filepath = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(mock_data)
            
            return {"success": True, "mockData": mock_data}

        except json.JSONDecodeError:
            return {"error": "ИИ вернул некорректный JSON"}, 400
        except Exception as e:
            current_app.logger.error(f"OpenRouter error: {str(e)}")
            return {"error": str(e)}, 500

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