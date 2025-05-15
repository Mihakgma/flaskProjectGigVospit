# Используем официальный образ Python в качестве базового
# Можно выбрать конкретную версию, например python:3.8-slim-buster
FROM python:3.8

# Устанавливаем рабочую директорию внутри контейнера
WORKDIR /app

# Копируем файл с зависимостями
# Если у вас requirements.txt:
#COPY requirements.txt .
# Если вы используете Poetry и файл pyproject.toml:
COPY pyproject.toml poetry.lock ./

# Устанавливаем зависимости
# Если используете pip:
#RUN #pip install --no-cache-dir -r requirements.txt
# Если используете poetry:
RUN pip install poetry && poetry install --no-dev --no-root

# Копируем весь остальной код проекта в рабочую директорию контейнера
COPY . .

# Устанавливаем переменные окружения (опционально, но полезно)
# Замените app.py на имя вашего основного файла приложения
ENV FLASK_APP=app.py/
# Режим продакшена
ENV FLASK_ENV=production/

# Убедитесь, что у вас установлен production-ready WSGI сервер
# Например, Gunicorn (для Linux) или Waitress (хорошо работает на Windows и в Docker)
# Если используете Waitress, добавьте его в requirements.txt/pyproject.toml
# pip install waitress

# Открываем порт, на котором будет работать приложение
EXPOSE 5000

# Команда для запуска приложения при старте контейнера
# Используйте production-ready сервер!
# Если используете Waitress (рекомендуется для Windows/кросс-платформы в Docker):
CMD ["waitress-serve", "--host=0.0.0.0", "--port=5000", "your_app_module:app"]
# Замените "your_app_module:app" на путь к вашему экземпляру Flask приложения.
# Например, если ваш app = Flask(__name__) находится в файле run.py в корне, то это может быть "run:app"
# Если app = Flask(__name__) находится в файле __init__.py внутри папки 'app', то это может быть "app:app"

# Если используете Gunicorn (чаще на Linux, но может работать и на Windows под Docker):
# CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:5000", "your_app_module:app"]
