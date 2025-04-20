from flask_wtf import FlaskForm
from wtforms import (StringField,
                     SelectField,
                     SubmitField,
                     BooleanField,
                     DateField,
                     TextAreaField,
                     PasswordField,
                     IntegerField,
                     SelectMultipleField)
from wtforms.validators import (DataRequired,
                                Length,
                                Email,
                                Optional,
                                EqualTo,
                                ValidationError)

from functions import validate_birth_date
from models import User, Role


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
    remember = BooleanField('Запомнить меня')
    submit = SubmitField('Войти')


from wtforms.validators import DataRequired, Length, Email, EqualTo, ValidationError
from wtforms.fields import StringField, PasswordField, SelectField, SubmitField
from models import User, Role  # Предположительно, модели расположены в отдельном модуле


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
    role = SelectField('Роль', coerce=int, validators=[DataRequired()])
    submit = SubmitField('Зарегистрироваться')

    def populate_role_choices(self):
        roles = Role.query.all()
        self.role.choices = [(role.id, role.name) for role in roles]  # Используем ID роли


class UserAddForm(FlaskForm):
    first_name = StringField('Имя', validators=[DataRequired()])
    last_name = StringField('Фамилия', validators=[DataRequired()])
    middle_name = StringField('Отчество')
    username = StringField('Имя пользователя', validators=[DataRequired(), Length(min=2, max=20)])
    user_code = StringField('Код пользователя', validators=[DataRequired(), Length(min=2, max=20)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Пароль', validators=[DataRequired(), Length(min=8)])
    confirm_password = PasswordField('Подтвердите пароль', validators=[DataRequired(), EqualTo('password')])
    phone = StringField('Телефон')
    dept_id = IntegerField('Отдел', validators=[DataRequired()])
    status_id = IntegerField('Статус', validators=[DataRequired()])
    role_ids = SelectMultipleField('Роли', coerce=int)
    submit = SubmitField('Добавить пользователя')

    def validate_username(self, username):
        user = User.query.filter_by(username=username.data).first()
        if user:
            raise ValidationError('Это имя пользователя уже занято.')

    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user:
            raise ValidationError('Этот email уже занят.')

    def validate_user_code(self, user_code):
        user = User.query.filter_by(user_code=user_code.data).first()
        if user:
            raise ValidationError('Этот код пользователя уже занят.')
