# database/db_instance.py
from flask_sqlalchemy import SQLAlchemy
# from sqlalchemy import create_engine
# from config import Config

# Создание движка SQLAlchemy
# engine = create_engine(
#     Config.DATABASE_URL,
#     echo=True,                 # Логирование SQL-запросов (для отладки)
#     pool_pre_ping=True,        # Проверяет наличие соединения перед использованием
#     pool_size=20,              # Максимальное количество постоянных соединений
#     max_overflow=10            # Допустимое превышение максимального количества соединений
# )

# Экземпляр SQLAlchemy
db = SQLAlchemy()
