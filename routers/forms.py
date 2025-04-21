from flask_wtf import FlaskForm
from wtforms import (StringField,
                     SelectField,
                     SubmitField,
                     BooleanField,
                     DateField,
                     TextAreaField,
                     PasswordField,
                     SelectMultipleField)
from wtforms.validators import (DataRequired,
                                Length,
                                Email,
                                Optional)
from wtforms_sqlalchemy.fields import (QuerySelectField,
                                       QuerySelectMultipleField)

from functions import validate_birth_date
from wtforms.widgets import CheckboxInput


class AddApplicantForm(FlaskForm):
    first_name = StringField('Имя', validators=[DataRequired(), Length(max=80)])
    last_name = StringField('Фамилия', validators=[DataRequired(), Length(max=80)])
    middle_name = StringField('Отчество', validators=[Length(max=80)])
    medbook_number = StringField('Номер медицинской книжки', validators=[Length(max=50)])
    snils_number = StringField('СНИЛС', validators=[Length(max=14)])
    passport_number = StringField('Номер паспорта', validators=[Length(max=20)])
    birth_date = DateField(
        'Дата рождения',
        format='%Y-%m-%d',
        validators=[
            DataRequired(),
            validate_birth_date
        ]
    )
    registration_address = StringField('Адрес регистрации', validators=[Length(max=200)])
    residence_address = StringField('Адрес проживания', validators=[Length(max=200)])
    phone_number = StringField('Телефон', validators=[Length(max=20)])  # Используем StringField
    email = StringField('Email', validators=[Optional(), Email(), Length(max=120)])  # Используем StringField
    contingent_id = SelectField('Контингент', coerce=int, validators=[DataRequired()])
    work_field_id = SelectField('Сфера деятельности', coerce=int, validators=[DataRequired()])
    applicant_type_id = SelectField('Тип заявителя', coerce=int, validators=[DataRequired()])
    attestation_type_id = SelectField('Тип аттестации', coerce=int, validators=[DataRequired()])
    submit = SubmitField('Добавить заявителя')


class AddContractForm(FlaskForm):
    number = StringField('Номер контракта', validators=[DataRequired(), Length(max=50)])
    contract_date = DateField('Дата заключения', format='%Y-%m-%d', validators=[DataRequired()])
    name = TextAreaField('Название контракта', validators=[DataRequired()])
    expiration_date = DateField('Дата истечения', format='%Y-%m-%d', validators=[Optional()])
    is_extended = BooleanField('Продлен')
    organization_id = SelectField('Организация', coerce=int, validators=[DataRequired()])
    additional_info = TextAreaField('Дополнительная информация')
    submit = SubmitField('Добавить контракт')


class LoginForm(FlaskForm):
    username = StringField('Имя пользователя', validators=[DataRequired()])
    password = PasswordField('Пароль', validators=[DataRequired()])
    remember_me = BooleanField('Запомнить меня')
    submit = SubmitField('Войти')


from wtforms.validators import DataRequired, Length, Email, EqualTo, ValidationError
from wtforms.fields import StringField, PasswordField, SubmitField
from models import User, Role, Department, Status, \
    Organization  # Предположительно, модели расположены в отдельном модуле


class RegistrationForm(FlaskForm):
    last_name = StringField('Фамилия', validators=[DataRequired(), Length(max=80)])
    first_name = StringField('Имя', validators=[DataRequired(), Length(max=80)])
    middle_name = StringField('Отчество', validators=[Length(max=80)], default='')
    username = StringField('Логин', validators=[
        DataRequired(),
        Length(min=2, max=20),
        # Валидатор уникальности логина
        lambda form, field: (
                                    User.query.filter_by(username=field.data).first() and
                                    ValidationError('Это имя пользователя уже занято. Пожалуйста, выберите другое.')
                            ) or True
    ])
    email = StringField('Электронная почта', validators=[
        DataRequired(),
        Email(),
        # Валидатор уникальности email
        lambda form, field: (
                                    User.query.filter_by(email=field.data).first() and
                                    ValidationError('Этот email уже занят. Пожалуйста, выберите другой.')
                            ) or True
    ])
    password = PasswordField('Пароль', validators=[DataRequired(), Length(min=8)])
    confirm_password = PasswordField('Подтверждение пароля', validators=[DataRequired(), EqualTo('password')])
    roles = SelectMultipleField('Роли', choices=[], widget=CheckboxInput())
    submit = SubmitField('Зарегистрироваться')

    def populate_role_choices(self):
        # roles = Role.query.all()
        self.roles.choices = [(role.id, role.name) for role in Role.query.all()]


class UserAddForm(FlaskForm):
    first_name = StringField('Имя', validators=[DataRequired()])
    last_name = StringField('Фамилия', validators=[DataRequired()])
    middle_name = StringField('Отчество')
    username = StringField('Имя пользователя', validators=[DataRequired(), Length(min=2, max=20)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Пароль', validators=[DataRequired(), Length(min=8)])
    # confirm_password = PasswordField('Подтвердите пароль', validators=[DataRequired(), EqualTo('password')])
    phone = StringField('Телефон')
    dept_id = QuerySelectField('Отдел',
                               query_factory=lambda: Department.query.all(),
                               get_label='name', allow_blank=True, blank_text='Выберите отдел')

    status_id = QuerySelectField('Статус',
                                 query_factory=lambda: Status.query.all(),
                                 get_label='name', allow_blank=True, blank_text='Выберите статус')
    roles = SelectMultipleField('Роли', choices=[], widget=CheckboxInput())
    info = TextAreaField('Дополнительно')  # Добавьте поле info
    submit = SubmitField('Добавить пользователя')

    def validate_username(self, username):
        user = User.query.filter_by(username=username.data).first()
        if user:
            raise ValidationError('Это имя пользователя уже занято.')

    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user:
            raise ValidationError('Этот email уже занят.')

    def populate_role_choices(self):
        roles = Role.query.all()
        self.roles.choices = [(role.id, role.name) for role in Role.query.all()]


class OrganizationAddForm(FlaskForm):
    name = StringField('Название организации', validators=[
        DataRequired(message="Обязательно введите название"),
        Length(max=200, message="Максимальное количество символов: 200")
    ])

    inn = StringField('ИНН', validators=[
        DataRequired(message="Обязательно введите ИНН"),
        Length(min=10, max=12, message="ИНН должен содержать 10 или 12 цифр")
    ])

    address = StringField('Адрес', validators=[
        Optional(),  # Адрес необязателен
        Length(max=200, message="Максимальное количество символов: 200")
    ])

    phone_number = StringField('Номер телефона', validators=[
        Optional(),  # Телефон необязателен
        Length(max=20, message="Максимальное количество символов: 20")
    ])

    email = StringField('Email', validators=[
        Optional(),  # Email необязателен
        Email(message="Некорректный адрес электронной почты"),
        Length(max=120, message="Максимальное количество символов: 120")
    ])

    is_active = BooleanField('Организация активна?', default=True)

    additional_info = TextAreaField('Дополнительная информация', validators=[
        Optional()  # Дополнительная информация необязательна
    ])

    submit = SubmitField('Сохранить')

    # Валидатор для проверки уникальности ИНН
    def validate_inn(self, field):
        organization = Organization.query.filter_by(inn=field.data).first()
        if organization:
            raise ValidationError("Организация с указанным ИНН уже зарегистрирована.")
