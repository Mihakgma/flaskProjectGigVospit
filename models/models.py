from werkzeug.security import check_password_hash

from database import db
from sqlalchemy import ForeignKey, Text, Table
from sqlalchemy.types import String, Integer, Boolean, DateTime
from flask_login import UserMixin  # Для интеграции с Flask-Login


# --- Модели ---

class Role(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)
    code = db.Column(db.String(10), unique=True, nullable=False)
    description = db.Column(Text)

    def __repr__(self):
        return f'<Role {self.name}>'


class Status(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)
    description = db.Column(Text)

    def __repr__(self):
        return f'<Status {self.name}>'


class Department(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)

    def __repr__(self):
        return f'<Department {self.name}>'


class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    last_name = db.Column(db.String(80), nullable=False)  # Фамилия
    first_name = db.Column(db.String(80), nullable=False)  # Имя
    middle_name = db.Column(db.String(80), nullable=True)  # Отчество
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(128), nullable=False)  # Пароль
    phone = db.Column(db.String(20), nullable=True)  # Телефон
    dept_id = db.Column(db.Integer, ForeignKey('department.id'), nullable=True)  # ID отдела
    status_id = db.Column(db.Integer, ForeignKey('status.id'), nullable=True)  # ID статуса
    department = db.relationship('Department', backref='users', lazy='joined')
    status = db.relationship('Status', backref='users', lazy='joined')
    is_logged_in = db.Column(db.Boolean, default=None, nullable=True)
    logged_in_time = db.Column(db.DateTime, default=None, nullable=True)
    last_commit_time = db.Column(db.DateTime, default=None, nullable=True)
    info = db.Column(db.Text(length=300), default=None, nullable=True)

    def get_id(self):  # Необходимо для Flask-Login
        return str(self.id)

    def check_password(self, password):
        """
        Проверяет, совпадает ли введённый пароль с сохранённым хешированным паролем.
        :param password: Пароль, введённый пользователем
        :return: True, если пароль верный, False в противном случае
        """
        return check_password_hash(self.password, password)


class ApplicantType(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(String(10), nullable=False)
    additional_info = db.Column(Text)


class Contingent(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(30), nullable=False)
    additional_info = db.Column(Text)


class WorkField(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    additional_info = db.Column(Text)


class AttestationType(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(String(10), nullable=False)
    additional_info = db.Column(Text)


class Organization(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(String(200), nullable=False)
    inn = db.Column(String(12), unique=True)  # 10 или 12 цифр для РФ
    address = db.Column(String(200))
    phone_number = db.Column(String(20))
    email = db.Column(String(120))
    is_active = db.Column(Boolean, nullable=False)
    additional_info = db.Column(Text)


class Contract(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    number = db.Column(String(50), nullable=False)
    contract_date = db.Column(DateTime, nullable=False)
    name = db.Column(Text)
    expiration_date = db.Column(DateTime)
    is_extended = db.Column(Boolean, nullable=False)
    organization_id = db.Column(Integer, ForeignKey('organization.id'))
    additional_info = db.Column(Text)
    # Определяем отношение один ко многим с таблицей Organization
    organization = db.relationship('Organization', backref='contracts')


# --- Таблицы связей ---

user_roles = Table('user_roles', db.metadata,
                   db.Column('user_id', db.Integer, db.ForeignKey('user.id')),
                   db.Column('role_id', db.Integer, db.ForeignKey('role.id'))
                   )

applicant_contract = Table(
    'applicant_contract', db.metadata,
    db.Column('applicant_id', db.Integer, db.ForeignKey('applicant.id'), primary_key=True),
    db.Column('contract_id', db.Integer, db.ForeignKey('contract.id'), primary_key=True)
)

# --- Relationships (после объявления таблиц связей) ---

User.roles = db.relationship('Role', secondary=user_roles, backref=db.backref('users', lazy=True))


class Applicant(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(String(80), nullable=False)
    last_name = db.Column(String(80), nullable=False)
    middle_name = db.Column(String(80), nullable=True)
    medbook_number = db.Column(String(50), unique=True, nullable=False)
    snils_number = db.Column(String(14), unique=True, nullable=False)  # 11 цифр + 3 разделителя
    passport_number = db.Column(String(20), nullable=True)  # 10 цифр (или 4+6)
    birth_date = db.Column(DateTime, nullable=False)
    registration_address = db.Column(String(200), nullable=True)
    residence_address = db.Column(String(200), nullable=True)
    phone_number = db.Column(String(20), nullable=True)
    email = db.Column(String(120), nullable=True)
    contingent_id = db.Column(Integer, ForeignKey('contingent.id'), nullable=False)
    work_field_id = db.Column(Integer, ForeignKey('work_field.id'), nullable=False)
    applicant_type_id = db.Column(Integer, ForeignKey('applicant_type.id'), nullable=False)
    attestation_type_id = db.Column(Integer, ForeignKey('attestation_type.id'), nullable=False)
    edited_by_user_id = db.Column(Integer, ForeignKey('user.id'), nullable=True)
    edited_time = db.Column(DateTime, nullable=True)
    is_editing_now = db.Column(Boolean, nullable=True)
    editing_by_id = db.Column(Integer, ForeignKey('user.id'), nullable=True)
    editing_started_at = db.Column(DateTime, nullable=True)
    contracts = db.relationship('Contract', secondary=applicant_contract, backref='applicants')
    contingent = db.relationship('Contingent', backref='applicants', lazy='joined')
    work_field = db.relationship('WorkField', backref='applicants', lazy='joined')
    applicant_type = db.relationship('ApplicantType', backref='applicants', lazy='joined')
    attestation_type = db.relationship('AttestationType', backref='applicants', lazy='joined')

    @property
    def full_name(self):
        """ Возвращает полное имя заявителя """
        parts = [self.last_name, self.first_name, self.middle_name]
        return ' '.join([part for part in parts if part]).strip()
