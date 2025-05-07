from app import app, db
from app.models import User, Dataset # Импортируем модели для создания таблиц

if __name__ == '__main__':
    with app.app_context():  # Создаем контекст приложения Flask
        db.create_all()  # Создаем таблицы в базе данных
    app.run(debug=True)