from app import app, db
from app.models import User, Dataset # Импортируем модели для создания таблиц

if __name__ == '__main__':
    with app.app_context():  # Создаем контекст приложения Flask
        from app.dashboard import create_dash_app
        dash_app = create_dash_app(app)

    app.run(debug=True)