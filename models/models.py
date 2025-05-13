from datetime import datetime

import pytz
from werkzeug.security import check_password_hash

from database import db
from sqlalchemy import ForeignKey, Table
from sqlalchemy.types import String, Integer, Boolean, DateTime, Text
from flask_login import UserMixin

from sqlalchemy.orm import validates
from sqlalchemy.exc import IntegrityError

nsk_tz = pytz.timezone('Asia/Novosibirsk')


def get_current_nsk_time():  # Переименовал для ясности
    """Возвращает текущее время в новосибирской временной зоне."""
    return datetime.now(nsk_tz)


class BaseModel(db.Model):
    __abstract__ = True  # Правильное имя атрибута для абстрактных моделей

    # Чтобы id всегда шел первым, определите его первым в классе.
    # SQLAlchemy обычно сохраняет порядок определения столбцов.
    id = db.Column(Integer, primary_key=True)

    created_at = db.Column(DateTime(timezone=True), default=get_current_nsk_time)
    updated_at = db.Column(DateTime(timezone=True), default=get_current_nsk_time, onupdate=get_current_nsk_time)
    info = db.Column(Text, default='')

    def __repr__(self):  # Правильное имя магического метода __repr__
        class_name = self.__class__.__name__  # Правильное получение имени класса
        if hasattr(self, 'name') and getattr(self, 'name') is not None:  # Добавил проверку на None
            return f"<{class_name}(id={self.id}, name='{self.name!r}')>"
        else:
            return f"<{class_name}(id={self.id})>"


class Role(BaseModel):
    name = db.Column(String(50), nullable=False)
    code = db.Column(String(10), unique=True, nullable=False)


class Status(BaseModel):
    name = db.Column(String(50), nullable=False)
    code = db.Column(String(7), nullable=False, unique=True)


class Department(BaseModel):
    name = db.Column(String(100), nullable=False)
    code = db.Column(String(5), nullable=False, unique=True)


class User(BaseModel, UserMixin):
    last_name = db.Column(String(80), nullable=False)  # Фамилия
    first_name = db.Column(String(80), nullable=False)  # Имя
    middle_name = db.Column(String(80), nullable=True)  # Отчество
    username = db.Column(String(80), unique=True, nullable=False)
    email = db.Column(String(120), unique=True, nullable=False)
    password = db.Column(String(128), nullable=False)  # Пароль
    phone = db.Column(String(11), nullable=True)  # Телефон
    dept_id = db.Column(Integer, ForeignKey('department.id'), nullable=False)  # ID отдела
    status_id = db.Column(Integer, ForeignKey('status.id'), nullable=False)  # ID статуса
    department = db.relationship('Department', backref='users', lazy='joined')
    status = db.relationship('Status', backref='users', lazy='joined')
    is_logged_in = db.Column(Boolean, default=False, nullable=True)
    logged_in_time = db.Column(DateTime(timezone=True), default=get_current_nsk_time, nullable=False)
    last_commit_time = db.Column(DateTime(timezone=True), default=get_current_nsk_time, nullable=False)

    def get_id(self):  # Необходимо для Flask-Login
        return str(self.id)

    def check_password(self, password):
        """
        Проверяет, совпадает ли введённый пароль с сохранённым хешированным паролем.
        :param password: Пароль, введённый пользователем
        :return: True, если пароль верный, False в противном случае
        """
        return check_password_hash(self.password, password)


class ApplicantType(BaseModel):
    name = db.Column(String(10), nullable=False)
    code = db.Column(String(3), nullable=False, unique=True)
    vizits = db.relationship('Vizit', back_populates='applicant_type')


class Contingent(BaseModel):
    name = db.Column(String(30), nullable=False)
    code = db.Column(String(5), nullable=False, unique=True)
    vizits = db.relationship('Vizit', back_populates='contingent')


class WorkField(BaseModel):
    name = db.Column(String(200), nullable=False)
    code = db.Column(String(10), nullable=False, unique=True)
    vizits = db.relationship('Vizit', back_populates='work_field')


class AttestationType(BaseModel):
    name = db.Column(String(10), nullable=False)
    code = db.Column(String(7), nullable=False, unique=True)
    vizits = db.relationship("Vizit", back_populates="attestation_type")


class Organization(BaseModel):
    name = db.Column(String(200), nullable=False)
    inn = db.Column(String(12), unique=True)
    address = db.Column(String(200))
    phone_number = db.Column(String(20))
    email = db.Column(String(120))
    is_active = db.Column(Boolean, nullable=False)
    created_by_user_id = db.Column(Integer, ForeignKey('user.id'),
                                   default=1,
                                   nullable=False)
    created_by_user = db.relationship('User', foreign_keys=[created_by_user_id])

    @validates('inn')
    def validate_inn(self, key, inn):
        if inn is not None:  # Проверяем только если inn не Null
            inn = str(inn).strip()  # Преобразуем в строку и удаляем пробелы
            if not (10 <= len(inn) <= 12) or not inn.isdigit():
                raise IntegrityError("ИНН должен содержать от 10 до 12 цифр.")

        return inn


class Contract(BaseModel):
    number = db.Column(String(50), nullable=False)
    contract_date = db.Column(DateTime(timezone=True), default=get_current_nsk_time, nullable=False)
    name = db.Column(Text, default=None, nullable=True)
    expiration_date = db.Column(DateTime(timezone=True), default=get_current_nsk_time, nullable=True)
    is_extended = db.Column(Boolean, nullable=False)
    organization_id = db.Column(Integer, ForeignKey('organization.id'))
    # Определяем отношение один ко многим с таблицей Organization
    organization = db.relationship('Organization', backref='contracts')
    created_by_user_id = db.Column(Integer, ForeignKey('user.id'),
                                   default=1,
                                   nullable=False)
    created_by_user = db.relationship('User', foreign_keys=[created_by_user_id])


user_roles = Table('user_roles', db.metadata,
                   db.Column('user_id', Integer, db.ForeignKey('user.id')),
                   db.Column('role_id', Integer, db.ForeignKey('role.id'))
                   )

User.roles = db.relationship('Role', secondary=user_roles, backref=db.backref('users', lazy=True))


class Applicant(BaseModel):
    first_name = db.Column(String(80), nullable=False)
    middle_name = db.Column(String(80), nullable=True)
    last_name = db.Column(String(80), nullable=False)
    medbook_number = db.Column(String(50), unique=True, nullable=False)
    snils_number = db.Column(String(11), unique=True, nullable=False)
    passport_number = db.Column(String(10), nullable=True)
    birth_date = db.Column(DateTime(timezone=True), default=get_current_nsk_time, nullable=False)
    registration_address = db.Column(String(200), nullable=True)
    residence_address = db.Column(String(200), nullable=True)
    phone_number = db.Column(String(11), nullable=True)
    email = db.Column(String(120), nullable=True)
    edited_by_user_id = db.Column(Integer, ForeignKey('user.id'), nullable=True)
    edited_by_user = db.relationship('User', foreign_keys=[edited_by_user_id])
    is_editing_now = db.Column(Boolean, nullable=True)
    editing_by_id = db.Column(Integer, ForeignKey('user.id'), nullable=True)
    editing_started_at = db.Column(DateTime(timezone=True), default=get_current_nsk_time, nullable=True)
    vizits = db.relationship('Vizit',
                             back_populates='applicant',  # Связывает с атрибутом 'applicant' в модели Vizit
                             cascade='all, delete-orphan',  # Если удалить Applicant, удалятся и все его Vizit
                             lazy='subquery')
    created_by_user_id = db.Column(Integer, ForeignKey('user.id'),
                                   default=1,
                                   nullable=False)
    created_by_user = db.relationship('User', foreign_keys=[created_by_user_id])

    @property
    def full_name(self):
        """ Возвращает полное имя заявителя """
        parts = [self.last_name, self.first_name, self.middle_name]
        return ' '.join([part for part in parts if part]).strip()


class Vizit(BaseModel):
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
