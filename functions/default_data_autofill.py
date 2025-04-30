from models.models import (Role, Status, Department, ApplicantType,
                           Contingent, WorkField, AttestationType,
                           Organization, Applicant, Vizit, applicant_vizit)

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
        "applicant_vizit.json": applicant_vizit
    }

    for filename, Model in model_map.items():
        filepath = os.path.join(data_dir, filename)
        if os.path.exists(filepath):
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                for id, entry in data.items():
                    try:
                        # При необходимости, можно привести id к int: int(id)
                        instance = Model(**entry)
                        if instance.__class__ == Applicant:
                            instance.birth_date = datetime.strptime(instance.birth_date,
                                                                    '%d.%m.%Y')
                        elif instance.__class__ == Vizit:
                            instance.created_at = datetime.strptime(instance.birth_date,
                                                                    '%d.%m.%Y')
                        db.session.add(instance)
                        db.session.commit()
                    except Exception as e:
                        db.session.rollback()
                        print(f"Error adding {Model.__name__} from {filename}: {entry}: {e}")
            except json.JSONDecodeError as e:
                print(f"Error decoding JSON in {filename}: {e}")
        else:
            print(f"File not found: {filepath}")


def db_load_data(db, data_dir="initial_data"):
    try:
        # db.create_all()
        load_initial_data(data_dir, db)
        print("Database initialized and data loaded successfully.")
    except Exception as e:
        print(f"Error initializing database: {e}")
