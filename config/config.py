import os
import secrets

from pathlib import Path

filename = 'config/db_conf_pg.txt'
try:
    with open(filename, 'r') as file:
        db_config_info = file.read().replace('\n', '')
except FileNotFoundError:
    db_config_info = None # Устанавливаем None, если файл не найден

# db_path = Path(__file__).resolve().parent.parent / 'example.db'


class Config:
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or db_config_info
    # SQLALCHEMY_DATABASE_URI = f'sqlite:///{db_path}'

    # Теперь SECRET_KEY всегда будет иметь значение:

    # либо из переменной окружения, либо сгенерированное (для локальной разработки)
    SECRET_KEY = os.environ.get('SECRET_KEY') or secrets.token_urlsafe(40)  # Увеличим длину для лучшей безопасности

    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Проверка на случай, если переменная окружения не установлена (опционально, но рекомендуется)
    if not SQLALCHEMY_DATABASE_URI:
        print("ВНИМАНИЕ: Переменная окружения 'DATABASE_URL' не установлена!")
        print("Не могу установить соединение с базой данных.")
        # В зависимости от приложения, вы можете здесь завершить работу
        # или подставить значение по умолчанию для локальной разработки (например, SQLite)
        print(f"Пытаюсь загрузить путь к БД из файла: <{filename}>")
        SQLALCHEMY_DATABASE_URI = db_config_info
        # или даже localhost, но тогда приложение упадет в Docker Compose без БД:
        # SQLALCHEMY_DATABASE_URI = "..."
        pass  # Оставляем None или предыдущее значение, если переменная не найдена

    SQLALCHEMY_TRACK_MODIFICATIONS = False
