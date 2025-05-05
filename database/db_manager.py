from sqlalchemy_utils import database_exists, create_database

from functions.default_db_data.default_data_autofill import db_load_data


def init_app(app, db):
    db.init_app(app)
    with app.app_context():
        db_url = app.config['SQLALCHEMY_DATABASE_URI']
        if not database_exists(db_url):
            create_database(db_url)
        db.create_all()
        db_load_data(db=db, data_dir="json/default_db_data")
