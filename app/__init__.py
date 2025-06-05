from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_wtf.csrf import CSRFProtect
import os
from dotenv import load_dotenv

load_dotenv() # Загружаем переменные окружения из .env файла

app = Flask(__name__)
app.config.from_object('config.Config') # Загружаем конфигурацию из config.py
db = SQLAlchemy(app)
migrate = Migrate(app, db)
csrf = CSRFProtect(app) # Эта строчка нужна для безопасности, с ней ничего делать не нужно
csrf._exempt_views.add('dash.dash.dispatch')

from app import models, routes # Импортируем модели и маршруты после инициализации db