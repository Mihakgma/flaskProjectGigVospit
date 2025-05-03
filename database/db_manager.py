import os

from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


def init_app(app):
    db.init_app(app)
    with app.app_context():
        if not os.path.exists(
                app.config['SQLALCHEMY_DATABASE_URI'].replace('sqlite:///', '')):  # Проверяем существование файла БД
            db.create_all()
            from functions.default_db_data.default_data_autofill import db_load_data
            db_load_data(db=db, data_dir="json/default_db_data")
