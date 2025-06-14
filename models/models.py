import os
from datetime import datetime

import pytz
from werkzeug.security import check_password_hash

from database import db
from sqlalchemy import Table, UniqueConstraint, event, Index
from sqlalchemy.types import String, Integer, Boolean, DateTime, Text
from flask_login import UserMixin

from sqlalchemy.orm import validates
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.declarative import declared_attr

from functions import check_if_exists

nsk_tz = pytz.timezone('Asia/Novosibirsk')


def get_current_nsk_time() -> datetime:
    """Возвращает текущее время в новосибирской временной зоне."""
    return datetime.now(nsk_tz)


def check_int(obj):
    if not type(obj) is int:
        raise ValueError("Ожидается целое число!")


def check_str(obj):
    if not type(obj) is str:
        raise ValueError("Ожидается строка!")


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
    last_activity_at = db.Column(DateTime(timezone=True), default=get_current_nsk_time, nullable=False)
    valid_ip = db.Column(String(15), nullable=True)
    tg_login = db.Column(String(15), nullable=True)  # имя логина в telegram начинается с @

    def get_id(self):  # Необходимо для Flask-Login
        return str(self.id)

    def check_password(self, password):
        """
        Проверяет, совпадает ли введённый пароль с сохранённым хешированным паролем.
        :param password: Пароль, введённый пользователем
        :return: True, если пароль верный, False в противном случае
        """
        return check_password_hash(self.password, password)

    @property
    def full_name(self):
        """ Возвращает полное имя заявителя """
        parts = [self.last_name, self.first_name, self.middle_name]
        return ' '.join([part for part in parts if part]).strip()

    @validates('tg_login')
    def validate_tg_login(self, key, tg_login):
        if tg_login is None:
            return tg_login
        check_str(tg_login)
        if not tg_login.startswith("@"):
            raise ValueError("Имя телеграм-аккаунта должно начинаться на @")
        return tg_login


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

    @validates('expiration_date')
    def validate_expiration_date(self, key, expiration_date):
        contract_date = self.contract_date
        if expiration_date is None:
            return expiration_date
        try:
            expiration_date_str = expiration_date.strftime("%d.%m.%Y")
            contract_date_str = contract_date.strftime("%d.%m.%Y")
        except AttributeError:
            # Обработка случая, когда contract_date или expiration_date не datetime
            raise ValueError("Некорректный формат даты в контракте или дате истечения.")
        if expiration_date < contract_date:
            raise ValueError(f'Дата истечения срока действия договора ({expiration_date_str}) '
                             f'не может быть раньше даты его подписания ({contract_date_str})')
        return expiration_date


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

    @validates('medbook_number')
    def validate_medbook_number(self, key, medbook_number):
        if medbook_number is not None:
            medbook_number = str(medbook_number).strip()
            if not len(medbook_number) == 12 or not medbook_number.isdigit():
                raise IntegrityError("Номер мед. книжки должен содержать 12 цифр.")
        return medbook_number

    @validates('snils_number')
    def validate_snils_number(self, key, snils_number):
        if snils_number is not None:
            snils_number = str(snils_number).strip()
            if not len(snils_number) == 11 or not snils_number.isdigit():
                raise IntegrityError("Номер СНИЛС должен содержать 11 цифр.")
        return snils_number


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


class AccessSetting(BaseModel):
    """
    Класс для таблицы, которая содержит информацию о настройках для
    1) page_lock_seconds - времени блокировки страниц для редактирования одной записи (с учетом таблицы и функции,
        с контролем через класс PageLocker), сек;
    2) activity_timeout_seconds - допустимого времени простоя пользователя (без проявления активности, т.е.
        без перехода по другим страницам приложения, контроль через класс UserCrudControl), сек;
    3) max_admins_number - максимальное количество пользователей с ролью admin;
    4) max_moders_number - максимальное количество пользователей с ролью moder;
    5) is_active_now - активирована ли сейчас данная настройка или нет;
    6) name - наименование настройки;
    7) activity_period_counter - с данным интервалом (количество нажатий всеми юзерами) будет осуществляться
        проверка на последнюю активность (время последней активности) каждым вошедшим в систему на данный момент.
        Срабатывает внутри декоратора role_required, который оборачивает
        функции-роуты для перехода на страницы приложения;
    8) activity_counter_max_threshold - с такой периодичностью (количество нажатий всеми юзерами) будет осуществляться
        завершение сессий всех активных на данный момент.

    При этом в текущей таблице БД одномоментно может быть только одна запись со значением поля
    is_active_now = True

    Метод get_activated_setting - получить строку таблицы (объект класса), у которого is_active_now = True.
    """

    __tablename__ = 'access_settings'

    id = db.Column(Integer, primary_key=True)
    name = db.Column(String(50), default="По умолчанию №1", nullable=True)
    page_lock_seconds = db.Column(Integer,
                                  default=300,
                                  nullable=False)
    activity_timeout_seconds = db.Column(Integer, default=900, nullable=False)
    max_admins_number = db.Column(Integer, default=1, nullable=False)
    max_moders_number = db.Column(Integer, default=2, nullable=False)
    is_active_now = db.Column(Boolean, default=False, nullable=False)
    activity_period_counter = db.Column(Integer, default=50, nullable=False)
    activity_counter_max_threshold = db.Column(Integer, default=1000, nullable=False)

    # Добавляем уникальный индекс с условием
    # Это обеспечит, что в таблице будет только одна запись с is_active_now = True
    ___table_args__ = (
        Index(
            'uix_only_one_activated_setting',  # Имя индекса
            'is_active_now',  # Имя колонки, по которой создается индекс
            unique=True,  # Делаем индекс уникальным
            # Условие для PostgreSQL
            postgresql_where=is_active_now == True
        ),
    )

    @validates('page_lock_seconds')
    def validate_page_lock_seconds(self, key, page_lock_seconds):
        time_low_boundary = 30
        time_up_boundary = 600
        if page_lock_seconds is None:
            raise IntegrityError("Необходимо указать максимально допустимое время доступа к страницам редактирования.")
        check_int(page_lock_seconds)
        if page_lock_seconds < time_low_boundary:
            raise ValueError("Максимально допустимое время доступа к страницам редактирования"
                             f" не может быть менее <{time_low_boundary}> секунд.")
        elif page_lock_seconds > time_up_boundary:
            raise ValueError("Максимально допустимое время доступа к страницам редактирования"
                             f" не может быть более <{time_up_boundary}> секунд.")
        return page_lock_seconds

    @validates('activity_timeout_seconds')
    def validate_activity_timeout_seconds(self, key, activity_timeout_seconds):
        time_low_boundary = 60
        time_up_boundary = 1800
        if activity_timeout_seconds is None:
            raise IntegrityError("Необходимо указать максимально допустимое время простоя пользователя.")
        check_int(activity_timeout_seconds)
        if activity_timeout_seconds < time_low_boundary:
            raise ValueError("Максимально допустимое время простоя пользователя не может быть менее "
                             f"<{time_low_boundary}> секунд.")
        elif activity_timeout_seconds > time_up_boundary:
            raise ValueError("Максимально допустимое время простоя пользователя"
                             f" не может быть более <{time_up_boundary}> секунд.")
        return activity_timeout_seconds

    @validates('max_admins_number')
    def validate_max_admins_number(self, key, max_admins_number):
        if max_admins_number is not None:
            check_int(max_admins_number)
            if max_admins_number < 1:
                raise ValueError("Максимальное количество пользователей с ролью администратор"
                                 " не может быть менее 1.")
            return max_admins_number

    @validates('max_moders_number')
    def validate_max_moders_number(self, key, max_moders_number):
        if max_moders_number is not None:
            check_int(max_moders_number)
            if max_moders_number < 1:
                raise ValueError("Максимальное количество пользователей с ролью модератор"
                                 " не может быть менее 1.")
            return max_moders_number

    @validates('activity_period_counter')
    def validate_activity_period_counter(self, key, activity_period_counter):
        clicks_low_boundary = 5
        clicks_up_boundary = 100
        if activity_period_counter is None:
            raise IntegrityError("Необходимо указать периодичность проверки активности пользователей.")
        check_int(activity_period_counter)
        if activity_period_counter < clicks_low_boundary:
            raise ValueError("Периодичность проверки активности пользователей"
                             f" не может быть менее <{clicks_low_boundary}> кликов.")
        elif activity_period_counter > clicks_up_boundary:
            raise ValueError("Периодичность проверки активности пользователей"
                             f" не может быть более <{clicks_up_boundary}> кликов.")
        return activity_period_counter

    @validates('activity_counter_max_threshold')
    def validate_activity_counter_max_threshold(self, key, activity_counter_max_threshold):
        clicks_low_boundary = 10
        clicks_up_boundary = 10000
        if activity_counter_max_threshold is None:
            raise IntegrityError("Необходимо указать периодичность проверки активности пользователей.")
        check_int(activity_counter_max_threshold)
        if activity_counter_max_threshold < clicks_low_boundary:
            raise ValueError("Периодичность обновления сессий пользователей"
                             f" не может быть менее <{clicks_low_boundary}> кликов.")
        if activity_counter_max_threshold < self.activity_period_counter:
            raise ValueError("Периодичность обновления сессий пользователей"
                             f" не может быть меньше периодичности проверки активности пользователей "
                             f"({self.activity_period_counter}) кликов.")
        elif activity_counter_max_threshold > clicks_up_boundary:
            raise ValueError("Периодичность обновления сессий пользователей"
                             f" не может быть более <{clicks_up_boundary}> кликов.")
        return activity_counter_max_threshold

    @staticmethod
    def get_activated_setting():
        return AccessSetting.query.filter_by(is_active_now=True).first()

    # --- Метод для строкового представления объекта (из предыдущих исправлений) ---
    def __repr__(self):
        return (f"<AccessSetting(id={self.id}, name='{self.name}', "
                f"is_active_now={self.is_active_now})>")


# --- Слушатели событий SQLAlchemy (из предыдущих исправлений) ---
@event.listens_for(AccessSetting, 'before_insert')
@event.listens_for(AccessSetting, 'before_update')
def receive_before_activate_setting(mapper, connection, target):
    """
    Слушатель, который срабатывает перед вставкой или обновлением объекта AccessSetting.
    Если is_active_now устанавливается в True для текущего объекта,
    он деактивирует все остальные настройки.
    """
    # Этот слушатель запускается до фактического коммита.
    # Если is_active_now меняется на True, мы деактивируем все остальные.
    if target.is_active_now:
        # Получаем текущую сессию SQLAlchemy, связанную с объектом
        session = db.session.object_session(target)
        if session is None:
            # Если объект не привязан к сессии (например, при прямом использовании connection)
            # В Flask-SQLAlchemy обычно всегда есть db.session.
            # Если у вас нет активной сессии, это может быть проблемой в инфраструктуре.
            # Для надежности, особенно в контексте Flask-SQLAlchemy,
            # можно использовать `db.session` напрямую.
            session = db.session  # Используем глобальную сессию Flask-SQLAlchemy

        # Находим все другие активные настройки, исключая текущую, если она уже существует
        query = session.query(AccessSetting).filter(
            AccessSetting.is_active_now == True
        )
        # Если target уже имеет ID, это означает, что это существующая запись, которую обновляют.
        # В этом случае мы исключаем ее из запроса, чтобы не деактивировать саму себя.
        if target.id is not None:
            query = query.filter(AccessSetting.id != target.id)

        other_active_settings = query.all()
        for setting in other_active_settings:
            # Деактивируем другие настройки.
            # Эти изменения будут отслеживаться сессией и зафиксированы вместе с target при commit.
            setting.is_active_now = False

        # Важное примечание: здесь НЕ НУЖЕН db.session.commit() или db.session.flush().
        # Изменения, внесенные в объекты, привязанные к сессии, будут зафиксированы
        # в той же транзакции, когда вызывается db.session.commit() для target.


class BackupSetting(BaseModel):
    """
    Данный класс применяется для создания (описания) таблицы БД, которая
    задает настройки сохранения таблиц БД:
    - периодичность (по умолч. 1 раз в 24 часа) "пробуждения";
    - условия (последняя активность, посл. БД-коммит пользователей + таймаут ожидания перед запуском сохранения +
      количество таймаутов после пробуждения);
    - файлы (таблицы) для сохранения;
    - корневая папка (директория) для хранения всех поддиректорий (по дате сохранения);
    - максимальный период хранения бэкап-папок с файлами (от 7 до 30 дней).

    Сохранять физически данные предполагается в файлах-json.
    При этом названия файлов берутся из названий таблиц БД.

    ДОБАВИТЬ:

    1) валидатор для check_times (количество чекаутов после пробуждения);
    2) валидатор для backup_local_dir (является ли реальным путем для текущего ПК с помощью либы Path)
    3) валидатор для backup_lan_dir (является ли реальным путем для текущей локальной сети, в которой состоит ПК
     с помощью либы Path, начинается ли на ip-адрес сервера и т.д.)

    """
    __tablename__ = 'backup_settings'

    id = db.Column(Integer, primary_key=True)
    name = db.Column(String(50), default="По умолчанию №1", nullable=False)
    period_secs = db.Column(Integer, default=86400, nullable=False)  # 24 hours
    check_period_secs = db.Column(Integer, default=3600, nullable=False)  # 1 hour
    check_times = db.Column(Integer, default=2, nullable=False)
    backup_local_dir = db.Column(String(200), nullable=False)
    backup_lan_dir = db.Column(String(200), nullable=False)
    is_active_now = db.Column(Boolean, default=False, nullable=False)
    backup_log = db.relationship('BackupLog', back_populates='backup_setting', lazy=True)
    lifespan_days = db.Column(Integer, default=7, nullable=False)

    @validates('period_secs')
    def validate_period_secs(self, key, period_secs):
        period_low_boundary = 300
        period_up_boundary = 86400 * 3
        if period_secs is None:
            raise IntegrityError("Необходимо указать периодичность ПРОБУЖДЕНИЯ для бэкапа БД.")
        check_int(period_secs)
        if period_secs < period_low_boundary:
            raise ValueError("Периодичность ПРОБУЖДЕНИЯ для бэкапа БД"
                             f" не может быть менее <{period_low_boundary}> секунд.")
        elif period_secs > period_up_boundary:
            raise ValueError("Периодичность ПРОБУЖДЕНИЯ для бэкапа БД"
                             f" не может быть более <{period_up_boundary}> секунд.")
        return period_secs

    @validates('check_period_secs')
    def validate_check_period_secs(self, key, check_period_secs):
        period_low_boundary = 90
        period_up_boundary = 3600 * 3
        period_secs_half = self.period_secs // 2
        if check_period_secs is None:
            raise IntegrityError("Необходимо указать периодичность проверки возможности бэкапа БД.")
        check_int(check_period_secs)
        if check_period_secs < period_low_boundary:
            raise ValueError("Периодичность проверки возможности  бэкапа БД (после ПРОБУЖДЕНИЯ)"
                             f" не может быть менее <{period_low_boundary}> секунд.")
        elif check_period_secs > period_secs_half:
            raise ValueError("Периодичность проверки возможности бэкапа БД (после ПРОБУЖДЕНИЯ)"
                             f" не может быть более ПОЛОВИНЫ <{period_secs_half}> (округл. до целого числа)"
                             f" от значения периодичности бэкапа <{self.period_secs}> секунд.")
        elif check_period_secs > period_up_boundary:
            raise ValueError("Периодичность проверки возможности бэкапа БД (после ПРОБУЖДЕНИЯ)"
                             f" не может быть более <{period_up_boundary}> секунд.")
        return check_period_secs

    @validates('check_times')
    def validate_check_times(self, key, check_times):
        times_low_boundary = 1
        times_up_boundary = 10
        period_secs_half = self.period_secs // 2
        check_period_secs = self.check_period_secs
        if check_times is None:
            raise IntegrityError("Необходимо указать количество проверок возможности бэкапа БД.")
        check_int(check_times)
        if check_times < times_low_boundary:
            raise ValueError("Количество проверок возможности бэкапа БД (после ПРОБУЖДЕНИЯ)"
                             f" не может быть менее <{check_times}> раз.")
        elif check_times * check_period_secs > period_secs_half:
            raise ValueError("Произведение количества чекаутов на продолжительность таймаута "
                             "между проверками возможности бэкапа"
                             f" не может быть более ПОЛОВИНЫ <{period_secs_half}> (округл. до целого числа)"
                             f" от значения периодичности бэкапа <{self.period_secs}> секунд.")
        elif check_times > times_up_boundary:
            raise ValueError("Количество проверок возможности бэкапа БД (после ПРОБУЖДЕНИЯ)"
                             f" не может быть более <{times_up_boundary}> раз.")
        return check_times

    @validates('backup_local_dir')
    def validate_backup_local_dir(self, key, backup_local_dir):
        if backup_local_dir:  # Если значение не None и не пустая строка
            # strip() удалит пробелы по краям
            clean_path = backup_local_dir.strip()
            if not clean_path:
                return None  # Если после удаления пробелов путь пуст, сохраняем как None

            if not os.path.isdir(clean_path):
                raise ValueError(f"Локальная директория '{clean_path}' не существует.")
            return clean_path
        return None  # Разрешаем None, если поле nullable=True и пользователь ничего не ввел

    @validates('backup_lan_dir')
    def validate_backup_lan_dir(self, key, backup_lan_dir):
        if backup_lan_dir:  # Если значение не None и не пустая строка
            clean_path = backup_lan_dir.strip()
            if not clean_path:
                return None  # Если после удаления пробелов путь пуст, сохраняем как None

            # Для сетевых путей os.path.isdir может не работать напрямую на всех ОС
            # или требовать монтирования. Для Windows UNC-путей (\\server\share)
            # os.path.isdir часто возвращает False, если путь не смонтирован.
            # Если это критично, возможно, потребуется более сложная проверка
            # или просто проверка формата пути, а не его существования.
            # Для простоты, пока используем os.path.isdir:
            if not os.path.isdir(clean_path):
                raise ValueError(f"Сетевая директория '{clean_path}' не существует или недоступна.")
            return clean_path
        return None  # Разрешаем None

    @validates('lifespan_days')
    def validate_lifespan_days(self, key, lifespan_days):
        min_days = 7
        max_days = 30
        if lifespan_days is None:
            raise ValueError("Необходимо указать период хранения бэкапов.")
        check_int(lifespan_days)
        if not (min_days <= lifespan_days <= max_days):
            raise ValueError(f"Период хранения бэкапов должен быть от {min_days} до {max_days} дней.")
        return lifespan_days

    @staticmethod
    def get_activated_setting():
        return BackupSetting.query.filter_by(is_active_now=True).first()


class BackupLog(BaseModel):
    """
    Данная таблица создана для хранения логов бэкапа.
    """
    __tablename__ = 'backup_log'

    id = db.Column(Integer, primary_key=True)
    started_at = db.Column(DateTime(timezone=True), default=get_current_nsk_time, nullable=False)
    ended_at = db.Column(DateTime(timezone=True), nullable=True)
    is_successful = db.Column(Boolean, default=False, nullable=False)
    total_size_mb = db.Column(Integer, default=0, nullable=False)
    backup_setting_id = db.Column(Integer, db.ForeignKey('backup_settings.id'), nullable=False)
    backup_setting = db.relationship('BackupSetting', back_populates='backup_log')
