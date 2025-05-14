from sqlalchemy.exc import IntegrityError

from models.models import (Role, Status, Department, ApplicantType,
                           Contingent, WorkField, AttestationType,
                           Organization, Applicant, Vizit, User)

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
        "user.json": User,
        "organization.json": Organization,
        "applicant.json": Applicant,
        "vizit.json": Vizit,
    }

    for filename, Model in model_map.items():
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

    # После добавления всех объектов свяжем applicants и visits
    # try:
    #     # Связывание посещений с заявителями
    #     for app in Applicant.query.all():
    #         for visit in Vizit.query.filter(Vizit.applicant_id == app.id).all():
    #             app.vizits.append(visit)
    #
    #     db.session.commit()  # Подтверждаем изменения
    #     print("Database initialized and data loaded successfully.")
    # except Exception as e:
    #     db.session.rollback()
    #     print(f"Error linking applicants to visits: {e}")

    # После добавления всех объектов свяжем пользователей и роли
    try:
        # Перечислим всех пользователей и соответствующие им роли последовательно
        users = User.query.order_by(User.id.asc()).all()
        roles = Role.query.order_by(Role.id.asc()).all()

        # Присваиваем каждой роли одного пользователя, соблюдая порядок ID
        for i, user in enumerate(users):
            if i < len(roles):
                user.roles.append(roles[i])

        db.session.commit()  # Подтверждаем изменения
        print("Пользователи и роли успешно связаны.")
    except Exception as e:
        db.session.rollback()
        print(f"Ошибка связывания пользователей и ролей: {e}")


def db_load_data(db, data_dir="initial_data"):
    try:
        # load_initial_data(data_dir, db)
        print("Database initialized and data loaded successfully.")
    except Exception as e:
        print(f"Error initializing database: {e}")
