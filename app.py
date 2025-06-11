from waitress import serve

from flask import Flask
from database import db, init_app
from models import User
from routers import (auth_bp,
                     routes_bp,
                     users_bp,
                     applicants_bp,
                     contracts_bp,
                     orgs_bp,
                     settings_bp,
                     visits_bp,
                     backup_settings_bp)  # Импортируем blueprint

# from flask_script import Manager
from flask_login import LoginManager
from flask_migrate import Migrate

from flask_wtf.csrf import CSRFProtect, generate_csrf


def create_app():
    app = Flask(__name__)
    # ... (ваша конфигурация)
    migrate = Migrate(app, db)
    app.config.from_object('config.Config')
    app.secret_key = app.config['SECRET_KEY']
    login_manager = LoginManager()
    login_manager.login_view = 'auth.login'  # Роут для входа, если пользователь не авторизован
    login_manager.init_app(app)
    csrf = CSRFProtect()
    csrf.init_app(app)

    # Контекстный процессор для CSRF-токена - ПЕРЕМЕСТИТЕ ЭТО СЮДА
    @app.context_processor
    def inject_csrf_token():
        return dict(csrf_token=generate_csrf)

    init_app(app, db=db)

    app.register_blueprint(auth_bp, url_prefix='/auth')

    @login_manager.user_loader
    def load_user(user_id):
        user = User.query.get(int(user_id))
        return user

    app.register_blueprint(users_bp, url_prefix='/users')
    app.register_blueprint(applicants_bp, url_prefix='/applicants')
    app.register_blueprint(contracts_bp, url_prefix='/contracts')
    app.register_blueprint(orgs_bp, url_prefix='/organizations')
    app.register_blueprint(settings_bp, url_prefix='/settings')
    app.register_blueprint(visits_bp, url_prefix='/visits')
    app.register_blueprint(backup_settings_bp, url_prefix='/backup_settings')
    app.register_blueprint(routes_bp, url_prefix='/')

    # app.config['WTF_CSRF_TIME_LIMIT'] = None
    return app


if __name__ == '__main__':
    app = create_app()
    # serve(app, host='0.0.0.0', port=5000)
    # ДЛЯ ОТЛАДКИ ПРИЛОЖЕНИЯ ЗАПУСКАЕМ В РЕЖИМЕ ДЕБАГГИНГА!!!
    app.run(debug=True)
