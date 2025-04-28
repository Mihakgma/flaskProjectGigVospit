import secrets
from waitress import serve

from flask import Flask
from database import init_app, db
from models import User
from routers import (auth_bp,
                     routes_bp,
                     users_bp,
                     applicants_bp)  # Импортируем blueprint

# from flask_script import Manager
from flask_login import LoginManager
from flask_migrate import Migrate

# from flask_wtf.csrf import CSRFProtect


def create_app():
    app = Flask(__name__)
    # ... (ваша конфигурация)
    migrate = Migrate(app, db)
    app.config.from_object('config.Config')  # Конфигурация из отдельного файла (см. ниже)
    app.secret_key = secrets.token_urlsafe(16)
    login_manager = LoginManager()
    login_manager.login_view = 'auth.login'  # Роут для входа, если пользователь не авторизован
    login_manager.init_app(app)
    init_app(app)
    app.register_blueprint(auth_bp, url_prefix='/auth')

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    app.register_blueprint(users_bp, url_prefix='/users')
    app.register_blueprint(applicants_bp, url_prefix='/applicants')
    app.register_blueprint(routes_bp, url_prefix='/')
    # csrf = CSRFProtect()
    # csrf.init_app(app)  # Инициализация CSRFProtect
    # app.config['WTF_CSRF_TIME_LIMIT'] = None
    return app


app = create_app()

if __name__ == '__main__':
    # serve(app, host='0.0.0.0', port=8080)
    # ДЛЯ ОТЛАДКИ ПРИЛОЖЕНИЯ ЗАПУСКАЕМ В РЕЖИМЕ ДЕБАГГИНГА!!!
    app.run(debug=True)
