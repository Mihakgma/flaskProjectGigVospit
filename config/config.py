import os


# Это чтение файла db_conf_pg.txt, вероятно, больше не нужно,
# если вы используете переменные окружения для настройки подключения.
# Если оно используется для чего-то другого, оставьте, но для подключения к БД в Docker Compose - удалите.
# with open('config/db_conf_pg.txt', 'r') as file:
#     db_config_info = file.read().replace('\n', '')

class Config:
    # Читаем строку подключения из переменной окружения DATABASE_URL
    # Если переменная не установлена (например, при локальной разработке без Docker Compose),
    # можно подставить значение по умолчанию или выбросить ошибку.
    # Для Docker Compose переменная ДОЛЖНА быть установлена.
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL')

    # Проверка на случай, если переменная окружения не установлена (опционально, но рекомендуется)
    if not SQLALCHEMY_DATABASE_URI:
        print("ВНИМАНИЕ: Переменная окружения 'DATABASE_URL' не установлена!")
        print("Не могу установить соединение с базой данных.")
        # В зависимости от приложения, вы можете здесь завершить работу
        # или подставить значение по умолчанию для локальной разработки (например, SQLite)
        # SQLALCHEMY_DATABASE_URI = "sqlite:///path/to/your/default.db"
        # или даже localhost, но тогда приложение упадет в Docker Compose без БД:
        # SQLALCHEMY_DATABASE_URI = "..."
        pass  # Оставляем None или предыдущее значение, если переменная не найдена

    # Эту строку (DATABASE_URL = ...) внутри класса Config можно удалить,
    # так как она не используется для настройки SQLAlchemy URI.
    # DATABASE_URL = "..."

    SQLALCHEMY_TRACK_MODIFICATIONS = False
