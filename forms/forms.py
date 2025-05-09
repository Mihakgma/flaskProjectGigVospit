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
                                EqualTo,
                                ValidationError,
                                Optional,
                                InputRequired)
from wtforms_sqlalchemy.fields import (QuerySelectField)

from functions import validate_birth_date
from wtforms.widgets import CheckboxInput, ListWidget

from functions.data_fix import (names_fix,
                                elmk_snils_fix, phone_number_fix)
from functions.validators.med_book_validator import validate_med_book
from functions.validators.snils_validator import validate_snils

from models import (User,
                    Role,
                    Department,
                    Status,
                    Organization,
                    AttestationType,
                    Contingent,
                    WorkField,
                    ApplicantType)
from models.models import Vizit, Contract


class AddApplicantForm(FlaskForm):
    first_name = StringField('Имя',
                             validators=[DataRequired(), Length(max=80)],
                             filters=(names_fix,))
    last_name = StringField('Фамилия',
                            validators=[DataRequired(), Length(max=80)],
                            filters=(names_fix,))
    middle_name = StringField('Отчество',
                              validators=[Length(max=80)],
                              filters=(names_fix,))
    medbook_number = StringField('Номер медицинской книжки',
                                 validators=[Length(max=50), validate_med_book],
                                 filters=(elmk_snils_fix,))
    snils_number = StringField('СНИЛС',
                               validators=[Length(max=14), validate_snils],
                               filters=(elmk_snils_fix,))
    passport_number = StringField('Номер паспорта', validators=[Length(max=20)])
    birth_date = DateField(
        'Дата рождения',
        format='%Y-%m-%d',
        validators=[
            DataRequired(),
            validate_birth_date
        ]
    )
    registration_address = StringField('Адрес регистрации',
                                       validators=[Length(max=200)],
                                       filters=(names_fix,))
    residence_address = StringField('Адрес проживания',
                                    validators=[Length(max=200)],
                                    filters=(names_fix,))
    phone_number = StringField('Телефон',
                               validators=[Length(max=20)],
                               filters=(phone_number_fix,))
    email = StringField('Email', validators=[Optional(), Email(), Length(max=120)])
    additional_info = TextAreaField('Дополнительная информация',
                                    validators=[
                                        Optional(),
                                        Length(max=300, message="Максимальное количество символов: 300")])
    submit = SubmitField('Добавить заявителя')


class LoginForm(FlaskForm):
    username = StringField('Имя пользователя', validators=[DataRequired()])
    password = PasswordField('Пароль', validators=[DataRequired()])
    remember_me = BooleanField('Запомнить меня')
    submit = SubmitField('Войти')


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
    roles = SelectMultipleField('Роли', choices=[], coerce=int,
                                widget=CheckboxInput())  # Коэрсируем строки в целые числа
    submit = SubmitField('Зарегистрироваться')

    def populate_role_choices(self):
        """Метод для наполнения списка доступных ролей"""
        roles = Role.query.all()
        self.roles.choices = [(role.id, role.name) for role in roles]


class UserAddForm(FlaskForm):
    first_name = StringField('Имя', validators=[DataRequired()])
    last_name = StringField('Фамилия', validators=[DataRequired()])
    middle_name = StringField('Отчество')
    username = StringField('Имя пользователя', validators=[DataRequired(), Length(min=2, max=20)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Пароль', validators=[DataRequired(), Length(min=8)])
    phone = StringField('Номер телефона', validators=[
        Optional(),
        Length(max=11, message="Максимальное количество символов: 11")
    ],
                        filters=(phone_number_fix,))
    dept_id = QuerySelectField('Отдел',
                               query_factory=lambda: Department.query.all(),
                               get_label='name', allow_blank=True, blank_text='Выберите отдел')

    status_id = QuerySelectField('Статус',
                                 query_factory=lambda: Status.query.all(),
                                 get_label='name', allow_blank=True, blank_text='Выберите статус')
    roles = SelectMultipleField('Роли', coerce=int, widget=ListWidget(prefix_label=False),
                                option_widget=CheckboxInput())
    info = TextAreaField('Дополнительно')
    submit = SubmitField('Добавить пользователя')

    def __init__(self, *args, **kwargs):
        super(UserAddForm, self).__init__(*args, **kwargs)
        self.roles.choices = [(role.id, role.name) for role in Role.query.all()]

    def validate_username(self, username):
        user = User.query.filter_by(username=username.data).first()
        if user:
            raise ValidationError('Это имя пользователя уже занято.')

    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user:
            raise ValidationError('Этот email уже занят.')


class OrganizationAddForm(FlaskForm):
    name = StringField('Название организации',
                       validators=[
                           DataRequired(message="Обязательно введите название"),
                           Length(max=200, message="Максимальное количество символов: 200")
                       ],
                       filters=(names_fix,))

    inn = StringField('ИНН',
                      validators=[
                          DataRequired(message="Обязательно введите ИНН"),
                          Length(min=10, max=12, message="ИНН должен содержать 10 или 12 цифр")
                      ],
                      filters=(elmk_snils_fix,))

    address = StringField('Адрес',
                          validators=[
                              Optional(),
                              Length(max=200, message="Максимальное количество символов: 200")],
                          filters=(names_fix,))

    phone_number = StringField('Номер телефона', validators=[
        Optional(),
        Length(max=20, message="Максимальное количество символов: 20")
    ],
                               filters=(phone_number_fix,))

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

    def validate_inn(self, field):
        organization = Organization.query.filter_by(inn=field.data).first()
        if organization:
            raise ValidationError("Организация с указанным ИНН уже зарегистрирована.")


def active_contracts_factory():
    # Можно добавить фильтр, например, только активные или не истекшие контракты
    return Contract.query.order_by(Contract.number).all()

class AddContractForm(FlaskForm):
    number = StringField('Номер договора', validators=[InputRequired()])
    contract_date = DateField('Дата подписания', format='%Y-%m-%d', validators=[InputRequired()])
    name = StringField('Название договора')
    expiration_date = DateField('Срок окончания', format='%Y-%m-%d')
    is_extended = BooleanField('Продлён')
    additional_info = TextAreaField('Дополнительная информация')
    # vizit_id = SelectField('Визит', coerce=int, choices=[])  # Новое поле
    organization_id = SelectField('Организация', coerce=int, choices=[])
    submit = SubmitField('Сохранить')

    def __init__(self, *args, **kwargs):
        super(AddContractForm, self).__init__(*args, **kwargs)
        self.organization_id.choices = [(o.id, o.name) for o in Organization.query.all()]
        # self.vizit_id.choices = [(v.id,
        #                           f"{v.applicant.last_name} {v.applicant.first_name} {v.applicant.middle_name} ({v.visit_date.strftime('%Y-%m-%d')})")
        #                          for v in Vizit.query.all()]


class VizitForm(FlaskForm):
    contingent_id = SelectField('Контингент', coerce=int, validators=[DataRequired()])
    attestation_type_id = SelectField('Тип аттестации', coerce=int, validators=[DataRequired()])
    work_field_id = SelectField('Сфера деятельности', coerce=int, validators=[DataRequired()])
    applicant_type_id = SelectField('Тип заявителя', coerce=int, validators=[DataRequired()])
    visit_date = DateField('Дата визита', validators=[DataRequired()])
    additional_info = TextAreaField('Дополнительная информация',
                                    validators=[
                                        Optional(),
                                        Length(max=300, message="Максимальное количество символов: 300")])
    contract = QuerySelectField(
        'Выберите контракт',
        query_factory=lambda: Contract.query.all(),  # Получаем все контракты
        get_label='number',  # Это поле будет отображаться в форме
        allow_blank=True,  # Позволяет не выбирать контракт, если не требуется
        blank_text='-- Не выбрано --',
        validators=[Optional()]
    )
    submit_visit = SubmitField('Добавить визит')

    def __init__(self, *args, **kwargs):
        super(VizitForm, self).__init__(*args, **kwargs)
        self.attestation_type_id.choices = [(a.id, a.name) for a in AttestationType.query.all()]
        self.contingent_id.choices = [(c.id, c.name) for c in Contingent.query.all()]
        self.work_field_id.choices = [(w.id, w.name) for w in WorkField.query.all()]
        self.applicant_type_id.choices = [(a.id, a.name) for a in ApplicantType.query.all()]


class ApplicantSearchForm(FlaskForm):
    last_name = StringField('Фамилия',
                            validators=[Optional()],
                            filters=(names_fix,))
    last_name_exact = BooleanField('Точное совпадение фамилии', default=False)  # Для полного совпадения
    snils_number = StringField('СНИЛС', validators=[Optional()])
    medbook_number = StringField('Номер медицинской книжки', validators=[Optional()])
    birth_date_start = DateField('Дата рождения (от)', validators=[Optional()])
    birth_date_end = DateField('Дата рождения (до)', validators=[Optional()])
    last_visit_start = DateField('Дата последнего визита (от)', validators=[Optional()])
    last_visit_end = DateField('Дата последнего визита (до)', validators=[Optional()])
    registration_address = StringField('Адрес регистрации',
                                       validators=[Optional()],
                                       filters=(names_fix,))
    residence_address = StringField('Адрес прописки',
                                    validators=[Optional()],
                                    filters=(names_fix,))
    edited_by_user = SelectField('Кем изменено последний раз', coerce=int, choices=[],
                                 validators=[Optional()])  # Поле для выбора пользователя
    edited_time_start = DateField('Дата последнего изменения (от)', format='%Y-%m-%d', validators=[Optional()])
    edited_time_end = DateField('Дата последнего изменения (до)', format='%Y-%m-%d', validators=[Optional()])
    submit = SubmitField('Найти')


class ApplicantEditForm(FlaskForm):
    first_name = StringField('Имя',
                             validators=[DataRequired(), Length(max=80)],
                             filters=(names_fix,))
    last_name = StringField('Фамилия',
                            validators=[DataRequired(), Length(max=80)],
                            filters=(names_fix,))
    middle_name = StringField('Отчество',
                              validators=[Length(max=80)],
                              filters=(names_fix,))
    medbook_number = StringField('Номер медицинской книжки',
                                 validators=[Length(max=50), validate_med_book],
                                 filters=(elmk_snils_fix,))
    snils_number = StringField('СНИЛС',
                               validators=[Length(max=14), validate_snils],
                               filters=(elmk_snils_fix,))
    passport_number = StringField('Номер паспорта', validators=[Length(max=20)])
    birth_date = DateField(
        'Дата рождения',
        format='%Y-%m-%d',
        validators=[
            DataRequired(),
            validate_birth_date
        ]
    )
    registration_address = StringField('Адрес регистрации',
                                       validators=[Length(max=200)],
                                       filters=(names_fix,))
    residence_address = StringField('Адрес проживания',
                                    validators=[Length(max=200)],
                                    filters=(names_fix,))
    phone_number = StringField('Телефон',
                               validators=[Length(max=20)],
                               filters=(phone_number_fix,))
    email = StringField('Email', validators=[Optional(), Email(), Length(max=120)])
    additional_info = TextAreaField('Дополнительная информация',
                                    validators=[
                                        Optional(),
                                        Length(max=300, message="Максимальное количество символов: 300")])
    submit = SubmitField('Сохранить')
