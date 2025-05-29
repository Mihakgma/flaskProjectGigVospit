from sqlalchemy_utils import database_exists, create_database
from models import User
# from config import Config
from functions.default_db_data.default_data_autofill import db_load_data

from utils.crud_classes import UserCrudControl


def init_app(app, db):
    db.init_app(app)
    with app.app_context():
        db_url = app.config['SQLALCHEMY_DATABASE_URI']
        if not database_exists(db_url):
            create_database(db_url)
        db.create_all()
        db_load_data(db=db, data_dir="json/default_db_data")
        # update users fields data with default values
        users = User.query.all()
        UserCrudControl.app_restart(db_obj=db,
                                    users=users,
                                    need_commit=True)
