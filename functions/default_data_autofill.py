from models.models import (Role, Status, Department, ApplicantType,
                           Contingent, WorkField, AttestationType,
                           Organization, Applicant, Vizit, User, user_roles)

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
        "contingent.json": Contingent,
        "attestation_type.json": AttestationType,
        "work_field.json": WorkField,
        "applicant_type.json": ApplicantType,
        "status.json": Status,
        "department.json": Department,
        "role.json": Role,
        "organization.json": Organization,
        "applicant.json": Applicant,
        "vizit.json": Vizit,
        "user.json": User
    }

    for filename, Model in model_map.items():
        filepath = os.path.join(data_dir, filename)
        if os.path.exists(filepath):
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    data = json.load(f)

                for id, entry in data.items():
                    try:
                        instance = Model(**entry)

                        # Преобразование дат для конкретных моделей
                        if isinstance(instance, Applicant):
                            instance.birth_date = datetime.strptime(entry.get('birth_date', ''), '%d.%m.%Y')

                        elif isinstance(instance, Vizit):
                            instance.created_at = datetime.strptime(entry.get('created_at', ''), '%d.%m.%Y')

                        # Сохраняем экземпляр в сессии
                        db.session.add(instance)

                    except Exception as e:
                        db.session.rollback()
                        print(f"Error adding {Model.__name__} from {filename}: {entry}: {e}")

            except json.JSONDecodeError as e:
                print(f"Error decoding JSON in {filename}: {e}")

    # После добавления всех объектов свяжем applicants и visits
    try:
        # Связывание посещений с заявителями
        for app in Applicant.query.all():
            for visit in Vizit.query.filter(Vizit.applicant_id == app.id).all():
                app.vizits.append(visit)

        db.session.commit()  # Подтверждаем изменения
        print("Database initialized and data loaded successfully.")
    except Exception as e:
        db.session.rollback()
        print(f"Error linking applicants to visits: {e}")

    # Теперь дополнительно загрузим данные в таблицу связи user_roles
    try:
        users_file_path = os.path.join(data_dir, "user.json")
        roles_file_path = os.path.join(data_dir, "role.json")

        if os.path.exists(users_file_path) and os.path.exists(roles_file_path):
            with open(users_file_path, 'r', encoding='utf-8') as uf, \
                    open(roles_file_path, 'r', encoding='utf-8') as rf:

                users_data = json.load(uf)
                roles_data = json.load(rf)

            # Предположим, что каждая роль имеет ассоциацию с одним или несколькими пользователями
            for user_id, user_entry in users_data.items():
                for role_id, _ in roles_data.items():  # Проходим по всем доступным ролям
                    db.session.execute(user_roles.insert(), {"user_id": int(user_id), "role_id": int(role_id)})

        db.session.commit()
        print("Данные успешно загружены и связаны.")

    except Exception as e:
        db.session.rollback()
        print(f"Ошибка связывания данных: {e}")


def db_load_data(db, data_dir="initial_data"):
    try:
        load_initial_data(data_dir, db)
        print("Database initialized and data loaded successfully.")
    except Exception as e:
        print(f"Error initializing database: {e}")
