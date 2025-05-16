from sqlalchemy_utils import database_exists, create_database

# from config import Config
from functions.default_db_data.default_data_autofill import db_load_data
# from sqlalchemy import create_engine

# engine = create_engine(
#     Config.DATABASE_URL,
#     echo=True,  # Логирование SQL-запросов (для отладки)
#     pool_pre_ping=True,  # Проверяет наличие соединения перед использованием
#     pool_size=20,  # Максимальное количество постоянных соединений
#     max_overflow=10  # Допустимое превышение максимального количества соединений
# )


def init_app(app, db):
    db.init_app(app)
    with app.app_context():
        db_url = app.config['SQLALCHEMY_DATABASE_URI']
        if not database_exists(db_url):
            create_database(db_url)
        db.create_all()
        db_load_data(db=db, data_dir="json/default_db_data")
