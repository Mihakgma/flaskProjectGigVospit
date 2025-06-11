from sqlalchemy import func
from sqlalchemy.exc import IntegrityError

from models import (Role, Status, Department, ApplicantType,
                    Contingent, WorkField, AttestationType,
                    Organization, Applicant, Vizit, User, TableDb, AccessSetting, BackupSetting)

import json
import os
import sys
from pathlib import Path
from datetime import datetime

# Получаем абсолютный путь к директории проекта
project_dir = Path(__file__).resolve().parent.parent

# Добавляем путь к директории проекта в sys.path
if str(project_dir) not in sys.path:
    sys.path.append(str(project_dir))


def load_initial_data(data_dir, db):
    model_map = {
        "access_setting.json": AccessSetting,
        "contingent.json": Contingent,
        "attestation_type.json": AttestationType,
        "work_field.json": WorkField,
        "applicant_type.json": ApplicantType,
        "status.json": Status,
        "department.json": Department,
        "role.json": Role,
        "user.json": User,
        "organization.json": Organization,
        "applicant.json": Applicant,
        # "vizit.json": Vizit,
        "table_db.json": TableDb,
        "backup_settings.json": BackupSetting,
    }

    for filename, Model in model_map.items():
        # Получаем имя таблицы из имени модели (для логов)
        model_name = Model.name if hasattr(Model, 'name') else Model.__name__

        # Проверяем, пуста ли текущая таблица
        try:
            # Используем func.count() для эффективного подсчета записей
            count = db.session.query(func.count(Model.id)).scalar()
            # Если модель не имеет поля 'id', можно использовать func.count() без аргументов
            # count = db.session.query(func.count()).select_from(Model).scalar()

            if count > 0:
                print(f"Таблица '{model_name}' не пуста ({count} записей). Пропускаем загрузку из {filename}.")
                continue  # Переходим к следующему файлу/модели в цикле
            else:
                print(f"Таблица '{model_name}' пуста. Начинаем загрузку из {filename}.")

        except Exception as e:
            print(f"Ошибка при проверке пустоты таблицы '{model_name}': {e}. Попытаемся загрузить данные.")
            # В случае ошибки при проверке, все равно пытаемся загрузить данные,
            # чтобы избежать блокировки инициализации при временных проблемах
        filepath = os.path.join(data_dir, filename)
        if os.path.exists(filepath):
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    data = json.load(f)

                for id, entry in data.items():
                    try:
                        filter_kwargs = {'id': int(id)}  # Или другое уникальное поле: 'code': entry.get('code')
                        existing_instance = db.session.query(Model).filter_by(**filter_kwargs).first()

                        if existing_instance:
                            print(f"Skipping existing {Model.__name__} with id {id}")
                            continue

                        instance = Model(**entry)

                        # Преобразование дат для конкретных моделей
                        if isinstance(instance, Applicant):
                            instance.birth_date = datetime.strptime(entry.get('birth_date', ''), '%d.%m.%Y')

                        elif isinstance(instance, Vizit):
                            instance.visit_date = datetime.strptime(entry.get('visit_date', ''), '%d.%m.%Y')

                        try:  # Отдельный try-except для db.session.add и commit
                            db.session.add(instance)
                            db.session.commit()
                        except IntegrityError as e:
                            db.session.rollback()
                            print(f"Integrity error adding {Model.__name__} from {filename}: {entry}: {e}")
                            # Продолжаем обработку следующих записей
                        except Exception as e:  # Другие ошибки при добавлении
                            db.session.rollback()
                            print(f"Error adding {Model.__name__} from {filename}: {entry}: {e}")
                            # Продолжаем обработку следующих записей
                    except Exception as e:  # Ошибки создания экземпляра модели
                        print(f"Error creating instance of {Model.__name__} from {filename}: {entry}: {e}")
                        # Продолжаем обработку следующих записей

            except json.JSONDecodeError as e:
                print(f"Error decoding JSON in {filename}: {e}")

    print("--- Проверка и создание связей пользователь-роль ---")
    try:
        # Пример связывания: Допустим, мы хотим связать каждого пользователя с ролью по их порядку ID
        # Или у вас есть более сложная логика связывания
        users = db.session.query(User).order_by(User.id.asc()).all()
        roles = db.session.query(Role).order_by(Role.id.asc()).all()

        # Пример простой логики связывания: связываем первого пользователя с первой ролью,
        # второго со второй и т.д., пока не закончатся пользователи или роли
        min_count = min(len(users), len(roles))

        linked_count = 0
        for i in range(min_count):
            user = users[i]
            role = roles[i]

            # !!! Важно: Проверяем, не имеет ли пользователь уже эту роль !!!
            # Это стандартный способ SQLAlchemy для M2M связей, который предотвращает дублирование.
            # Если связь уже есть, user.roles.append(role) просто ничего не сделает.
            if role not in user.roles:
                print(f"Создаем связь: Пользователь '{user.username}' с ролью '{role.name}'")
                user.roles.append(role)
                linked_count += 1
            else:
                print(f"Связь уже существует: Пользователь '{user.username}' уже имеет роль '{role.name}'. Пропускаем.")

        # Коммитим изменения после создания всех связей
        if linked_count > 0:
            try:
                db.session.commit()
                print(f"Успешно создано {linked_count} новых связей пользователь-роль.")
            except IntegrityError as e:
                db.session.rollback()
                print(
                    f"Ошибка целостности при коммите связей пользователь-роль: {e}. "
                    f"Возможно, были добавлены дубликаты несмотря на проверку 'if role not in user.roles'.")
            except Exception as e:
                db.session.rollback()
                print(f"Неизвестная ошибка при коммите связей пользователь-роль: {e}")
        else:
            print("Новые связи пользователь-роль не требовалось создавать.")

    except Exception as e:
        # Общая ошибка при получении пользователей/ролей или при связывании
        print(f"Ошибка при создании связей пользователь-роль: {e}")
        db.session.rollback()  # Откатываем сессию на всякий случай


def db_load_data(db, data_dir="initial_data"):
    try:
        load_initial_data(data_dir, db)
        print("Database initialized and data loaded successfully.")
    except Exception as e:
        print(f"Error initializing database: {e}")
