import secrets

from flask import Flask
from database import init_app
from routers import routes_bp  # Импортируем blueprint

app = Flask(__name__)
app.config.from_object('config.Config')  # Конфигурация из отдельного файла (см. ниже)
app.secret_key = secrets.token_urlsafe(16)
init_app(app)  # Инициализируем базу данных

app.register_blueprint(routes_bp, url_prefix='/')  # Регистрируем blueprint

if __name__ == '__main__':
    app.run(debug=True)
