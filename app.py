import secrets
from waitress import serve

from flask import Flask
from database import init_app
from routers import routes_bp  # Импортируем blueprint

from flask_wtf.csrf import CSRFProtect


def create_app():
    app = Flask(__name__)
    # ... (ваша конфигурация)

    app.config.from_object('config.Config')  # Конфигурация из отдельного файла (см. ниже)
    app.secret_key = secrets.token_urlsafe(16)
    init_app(app)  # Инициализируем базу данных

    app.register_blueprint(routes_bp, url_prefix='/')  # Регистрируем blueprint
    csrf = CSRFProtect()
    csrf.init_app(app)  # Инициализация CSRFProtect
    return app


app = create_app()

if __name__ == '__main__':
    serve(app, host='0.0.0.0', port=8080)
    # ДЛЯ ОТЛАДКИ ПРИЛОЖЕНИЯ ЗАПУСКАЕМ В РЕЖИМЕ ДЕБАГГИНГА!!!
    # app.run(debug=True)
