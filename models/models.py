from datetime import datetime

import pytz
from werkzeug.security import check_password_hash

from database import db
from sqlalchemy import Table, UniqueConstraint
from sqlalchemy.types import String, Integer, Boolean, DateTime, Text
from flask_login import UserMixin

from sqlalchemy.orm import validates
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.declarative import declared_attr

from functions import check_if_exists

nsk_tz = pytz.timezone('Asia/Novosibirsk')


def get_current_nsk_time():
    """Возвращает текущее время в новосибирской временной зоне."""
    return datetime.now(nsk_tz)


class BaseModel(db.Model):
    __abstract__ = True

    created_at = db.Column(DateTime(timezone=True), default=get_current_nsk_time)
    updated_at = db.Column(DateTime(timezone=True), default=get_current_nsk_time, onupdate=get_current_nsk_time)
    info = db.Column(Text, default='')

    def __repr__(self):
        class_name = self.__class__.__name__
        if hasattr(self, 'name') and getattr(self, 'name') is not None:
            return f"<{class_name}(id={self.id}, name='{self.name!r}')>"
        else:
            return f"<{class_name}(id={self.id})>"


class Role(BaseModel):
    id = db.Column(Integer, primary_key=True)
    name = db.Column(String(50), nullable=False)
    code = db.Column(String(10), unique=True, nullable=False)


class Status(BaseModel):
    id = db.Column(Integer, primary_key=True)
    name = db.Column(String(50), nullable=False)
    code = db.Column(String(7), nullable=False, unique=True)


class Department(BaseModel):
    id = db.Column(Integer, primary_key=True)
    name = db.Column(String(100), nullable=False)
    code = db.Column(String(5), nullable=False, unique=True)


class User(BaseModel, UserMixin):
    id = db.Column(Integer, primary_key=True)
    last_name = db.Column(String(80), nullable=False)
    first_name = db.Column(String(80), nullable=False)
    middle_name = db.Column(String(80), nullable=True)
    username = db.Column(String(80), unique=True, nullable=False)
    email = db.Column(String(120), unique=True, nullable=False)
    password = db.Column(String(128), nullable=False)
    phone_number = db.Column(String(11), nullable=True)
    dept_id = db.Column(Integer, db.ForeignKey('department.id'), nullable=False)
    status_id = db.Column(Integer, db.ForeignKey('status.id'), nullable=False)
    department = db.relationship('Department', backref='users', lazy='joined')
    status = db.relationship('Status', backref='users', lazy='joined')
    is_logged_in = db.Column(Boolean, default=False, nullable=True)
    logged_in_at = db.Column(DateTime(timezone=True), default=get_current_nsk_time, nullable=False)
    last_commit_at = db.Column(DateTime(timezone=True), default=get_current_nsk_time, nullable=False)
    valid_ip = db.Column(String(15), nullable=True)

    def get_id(self):  # Необходимо для Flask-Login
        return str(self.id)

    def check_password(self, password):
        """
        Проверяет, совпадает ли введённый пароль с сохранённым хешированным паролем.
        :param password: Пароль, введённый пользователем
        :return: True, если пароль верный, False в противном случае
        """
        return check_password_hash(self.password, password)


class CrudInfoModel:

    @declared_attr
    def created_by_user_id(cls):
        return db.Column(Integer,
                         db.ForeignKey('user.id'),  # Используйте db.ForeignKey
                         default=1,
                         nullable=False)

    # Отношения (relationships) ДОЛЖНЫ быть с @declared_attr в миксинах
    @declared_attr
    def created_by_user(cls):
        return db.relationship('User',
                               foreign_keys=[cls.created_by_user_id])

    @declared_attr
    def updated_by_user_id(cls):
        return db.Column(Integer,
                         db.ForeignKey('user.id'),  # Используйте db.ForeignKey
                         default=1,
                         nullable=False)

    @declared_attr
    def updated_by_user(cls):
        # В relationship внутри @declared_attr миксина,
        # нужно явно указывать foreign_keys и использовать cls.имя_колонки
        return db.relationship('User',
                               foreign_keys=[cls.updated_by_user_id])


class TableDb(db.Model):
    __tablename__ = 'table_db'  # Явное имя таблицы

    id = db.Column(Integer, primary_key=True)
    # Используем рассчитанную максимальную длину и уникальность
    name = db.Column(String(20), unique=True, nullable=False)

    def __repr__(self):
        return f"<TableDb (id={self.id}, name={self.name!r})>"


class EditLog(db.Model):
    __tablename__ = 'edit_log'  # Явное имя таблицы
    id = db.Column(Integer, primary_key=True)
    table_db_id = db.Column(Integer, db.ForeignKey('table_db.id'), nullable=False)
    table_db = db.relationship('TableDb')  # Отношение для удобного доступа к имени таблицы
    # ID обновленной записи в другой таблице (без внешнего ключа, как запрошено)
    updated_row_id = db.Column(Integer, nullable=False)
    # Время обновления
    row_updated_at = db.Column(DateTime(timezone=True),
                               default=get_current_nsk_time,  # Используем вашу функцию времени
                               nullable=False)
    # Пользователь, который внес изменение в указанную таблицу
    updated_by_user_id = db.Column(Integer, db.ForeignKey('user.id'), nullable=False)
    updated_by_user = db.relationship('User')  # Отношение для удобного доступа к пользователю
    # Дополнительная информация/заметки пользователя
    info = db.Column(Text, default='')

    def __repr__(self):
        return (f"<EditLog(id={self.id}, "
                f"table='{self.table_db.name if self.table_db else 'N/A'}', "
                f"row_id={self.updated_row_id}, "
                f"row_updated_at={self.row_updated_at})>")


class ApplicantType(BaseModel):
    id = db.Column(Integer, primary_key=True)
    name = db.Column(String(10), nullable=False)
    code = db.Column(String(3), nullable=False, unique=True)
    vizits = db.relationship('Vizit', back_populates='applicant_type')


class Contingent(BaseModel):
    id = db.Column(Integer, primary_key=True)
    name = db.Column(String(30), nullable=False)
    code = db.Column(String(5), nullable=False, unique=True)
    vizits = db.relationship('Vizit', back_populates='contingent')


class WorkField(BaseModel):
    id = db.Column(Integer, primary_key=True)
    name = db.Column(String(200), nullable=False)
    code = db.Column(String(10), nullable=False, unique=True)
    vizits = db.relationship('Vizit', back_populates='work_field')


class AttestationType(BaseModel):
    id = db.Column(Integer, primary_key=True)
    name = db.Column(String(10), nullable=False)
    code = db.Column(String(7), nullable=False, unique=True)
    vizits = db.relationship("Vizit", back_populates="attestation_type")


class Organization(BaseModel, CrudInfoModel):
    id = db.Column(Integer, primary_key=True)
    name = db.Column(String(200), nullable=False)
    inn = db.Column(String(12), unique=True)
    address = db.Column(String(200))
    phone_number = db.Column(String(20))
    email = db.Column(String(120))
    is_active = db.Column(Boolean, nullable=False)

    @validates('inn')
    def validate_inn(self, key, inn):
        if inn is not None:
            inn = str(inn).strip()
            if not (10 <= len(inn) <= 12) or not inn.isdigit():
                raise IntegrityError("ИНН должен содержать от 10 до 12 цифр.")

        return inn

        # Метод для преобразования объекта в словарь (для AJAX ответов)

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'inn': self.inn,
            'address': self.address,
            'phone_number': self.phone_number,
            'email': self.email,
            'is_active': self.is_active,
            'info': getattr(self, 'info', None),
            # Учитываем, что info может быть из CrudInfoModel или отсутствовать
            # Возможно, добавить поля из CrudInfoModel если они нужны на фронтенде
            'created_at': self.created_at.isoformat() if hasattr(self, 'created_at') and self.created_at else None,
            'updated_at': self.updated_at.isoformat() if hasattr(self, 'updated_at') and self.updated_at else None,
            'created_by_id': self.created_by_id if hasattr(self, 'created_by_id') else None,
        }

    @property
    def show_info(self):
        out_info = (f"Наименование: <{check_if_exists(self.name)}>, "
                    f"ИНН: <{check_if_exists(self.inn)}>, "
                    f"email: <{check_if_exists(self.email)}>")
        return out_info


class Contract(BaseModel, CrudInfoModel):
    id = db.Column(Integer, primary_key=True)
    number = db.Column(String(50), nullable=False)
    contract_date = db.Column(DateTime(timezone=True), default=get_current_nsk_time, nullable=False)
    name = db.Column(Text, default=None, nullable=True)
    expiration_date = db.Column(DateTime(timezone=True), default=get_current_nsk_time, nullable=True)
    is_extended = db.Column(Boolean, nullable=False)
    organization_id = db.Column(Integer, db.ForeignKey('organization.id'))
    # Определяем отношение один ко многим с таблицей Organization
    organization = db.relationship('Organization', backref='contracts')

    __table_args__ = (
        UniqueConstraint('number',
                         'contract_date',
                         'organization_id',
                         name='unique_contract_constraint'),
    )

    @property
    def show_info(self):
        out_info = (f"Номер: <{check_if_exists(self.number)}> "
                    f"Наименование: <{check_if_exists(self.name)}> "
                    f"(Организация: {self.organization.show_info})")
        return out_info


user_roles = Table('user_roles', db.metadata,
                   # Указываем user_id как часть первичного ключа
                   db.Column('user_id', Integer, db.ForeignKey('user.id'), primary_key=True),
                   # Указываем role_id как часть первичного ключа
                   db.Column('role_id', Integer, db.ForeignKey('role.id'), primary_key=True)
                   # Композитный первичный ключ (user_id, role_id) автоматически обеспечивает уникальность этой пары
                   )

User.roles = db.relationship('Role', secondary=user_roles, backref=db.backref('users', lazy=True))


class Applicant(BaseModel, CrudInfoModel):
    id = db.Column(Integer, primary_key=True)
    first_name = db.Column(String(80), nullable=False)
    middle_name = db.Column(String(80), nullable=True)
    last_name = db.Column(String(80), nullable=False)
    medbook_number = db.Column(String(12),
                               unique=True,
                               nullable=False,
                               index=True)
    snils_number = db.Column(String(11),
                             unique=True,
                             nullable=False,
                             index=True)
    passport_number = db.Column(String(10), nullable=True)
    birth_date = db.Column(DateTime(timezone=True),
                           default=get_current_nsk_time,
                           nullable=False)
    registration_address = db.Column(String(200), nullable=True)
    residence_address = db.Column(String(200), nullable=True)
    phone_number = db.Column(String(11), nullable=True)
    email = db.Column(String(120), nullable=True)
    vizits = db.relationship('Vizit',
                             back_populates='applicant',  # Связывает с атрибутом 'applicant' в модели Vizit
                             cascade='all, delete-orphan',  # Если удалить Applicant, удалятся и все его Vizit
                             lazy='subquery')

    @property
    def full_name(self):
        """ Возвращает полное имя заявителя """
        parts = [self.last_name, self.first_name, self.middle_name]
        return ' '.join([part for part in parts if part]).strip()

    @property
    def censored_search_info(self):
        parts = [self.last_name, self.first_name, self.middle_name]
        fio_cens = '. '.join([part[0] if part else " " for part in parts])
        birth_date_str = '-'
        if self.birth_date:
            birth_date_str = self.birth_date.strftime('%d.%m.%Y')
        num_vizits = len(self.vizits) if self.vizits is not None else 0
        out_info = (f"{fio_cens}, "
                    f"д.р.: {birth_date_str}, "
                    f"м.к.: {self.medbook_number}, "
                    f"СНИЛС: {self.snils_number}, "
                    f"тел.: {check_if_exists(self.phone_number)}, "
                    f"email: {check_if_exists(self.email)}, "
                    f"визитов всего: {num_vizits}")
        return out_info


class Vizit(BaseModel, CrudInfoModel):
    id = db.Column(Integer, primary_key=True)
    applicant_id = db.Column(Integer, db.ForeignKey('applicant.id'), nullable=False)
    applicant = db.relationship('Applicant', back_populates='vizits')
    visit_date = db.Column(DateTime(timezone=True), default=get_current_nsk_time, nullable=False)  # Дата оформления
    contingent_id = db.Column(Integer, db.ForeignKey('contingent.id'), nullable=False)
    attestation_type_id = db.Column(Integer, db.ForeignKey('attestation_type.id'), nullable=False)
    work_field_id = db.Column(Integer, db.ForeignKey('work_field.id'), nullable=False)
    applicant_type_id = db.Column(Integer, db.ForeignKey('applicant_type.id'), nullable=False)
    contingent = db.relationship('Contingent', back_populates='vizits')
    attestation_type = db.relationship('AttestationType', back_populates='vizits')
    work_field = db.relationship('WorkField', back_populates='vizits')
    applicant_type = db.relationship('ApplicantType', back_populates='vizits')
    contract_id = db.Column(Integer, db.ForeignKey('contract.id'), nullable=True)
    contract = db.relationship('Contract',
                               backref=db.backref('vizits', cascade=None),
                               lazy='subquery')
