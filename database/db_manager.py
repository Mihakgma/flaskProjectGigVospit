from sqlalchemy_utils import database_exists, create_database

from models import User, BackupSetting
from functions.default_db_data.default_data_autofill import db_load_data
from utils.backup_management.backup_manager import BackupManager
from utils.crud_classes import UserCrudControl
from utils.pages_lock.lock_management import PageLocker


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
        UserCrudControl.sessions_restart(db_obj=db, users=users, need_commit=True)
        PageLocker.clear_all_lock_info()

        # Запуск BackupManager в фоне
        # setting = BackupSetting.get_activated_setting()
        # if setting:
        #     backup_manager = BackupManager(active_backup_setting=setting,
        #                                    flask_app=app,
        #                                    testing=True)
        #     backup_manager.start()
        #     app.extensions['backup_manager'] = backup_manager
