import os

from flask_wtf import FlaskForm
from wtforms import (StringField,
                     SelectField,
                     SubmitField,
                     BooleanField,
                     DateField,
                     TextAreaField,
                     PasswordField,
                     SelectMultipleField, validators)
from wtforms.fields.numeric import IntegerField
from wtforms.validators import (DataRequired,
                                Length,
                                Email,
                                ValidationError,
                                Optional,
                                InputRequired, Regexp, NumberRange)
from wtforms_sqlalchemy.fields import (QuerySelectField)

from functions import validate_birth_date
from wtforms.widgets import CheckboxInput, ListWidget

from functions.data_fix import (names_fix,
                                elmk_snils_fix,
                                phone_number_fix,
                                address_names_fix)
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
                    ApplicantType,
                    Contract)


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
    info = TextAreaField('Дополнительная информация',
                         validators=[
                             Optional(),
                             Length(max=300, message="Максимальное количество символов: 300")])
    submit = SubmitField('Добавить заявителя')


class LoginForm(FlaskForm):
    username = StringField('Имя пользователя', validators=[DataRequired()])
    password = PasswordField('Пароль', validators=[DataRequired()])
    remember_me = BooleanField('Запомнить меня')
    submit = SubmitField('Войти')


class UserForm(FlaskForm):  # Переименовали для общего использования
    first_name = StringField('Имя', validators=[DataRequired(message="Поле 'Имя' обязательно для заполнения.")])
    last_name = StringField('Фамилия', validators=[DataRequired(message="Поле 'Фамилия' обязательно для заполнения.")])
    middle_name = StringField('Отчество')
    username = StringField('Имя пользователя (логин)',
                           validators=[DataRequired(message="Поле 'Имя пользователя' обязательно для заполнения."),
                                       Length(min=2, max=20)])
    email = StringField('Email', validators=[DataRequired(message="Поле 'Email' обязательно для заполнения."),
                                             Email(message="Некорректный формат email.")])
    password = PasswordField('Пароль',
                             validators=[Optional(), Length(min=8, message="Пароль должен быть не менее 8 символов.")])
    phone_number = StringField('Номер телефона', validators=[
        Optional(),
        Length(max=11, message="Номер телефона не должен превышать 11 символов.")
    ],
                               filters=(phone_number_fix,))
    dept_id = QuerySelectField('Отдел',
                               query_factory=lambda: Department.query.order_by(Department.name).all(),
                               get_label='name',
                               allow_blank=False,  # Если отдел всегда должен быть выбран
                               validators=[DataRequired(message="Необходимо выбрать отдел.")]
                               )
    status_id = QuerySelectField('Статус',
                                 query_factory=lambda: Status.query.order_by(Status.name).all(),
                                 get_label='name',
                                 allow_blank=False,  # Если статус всегда должен быть выбран
                                 validators=[DataRequired(message="Необходимо выбрать статус.")]
                                 )
    roles = SelectMultipleField('Роли',
                                coerce=int,
                                widget=ListWidget(prefix_label=False),
                                option_widget=CheckboxInput(),
                                validators=[DataRequired(message="Выберите хотя бы одну роль.")]
                                )
    info = TextAreaField('Дополнительная информация')
    submit = SubmitField('Сохранить')  # Кнопка будет 'Добавить' или 'Сохранить изменения' в зависимости от контекста

    def __init__(self, *args, original_username=None, original_email=None, **kwargs):
        super(UserForm, self).__init__(*args, **kwargs)
        self.original_username = original_username
        self.original_email = original_email
        # Заполняем choices для ролей, если они еще не установлены (например, при GET)
        # или если они были сброшены (при создании формы с request.form при POST)
        if not self.roles.choices or not args:
            self.roles.choices = [(role.id, role.name) for role in Role.query.order_by(Role.name).all()]
            if not self.roles.choices:  # Если ролей в БД нет вообще
                self.roles.choices = []

    def validate_username(self, username_field):
        # Если имя пользователя не изменилось, и мы редактируем существующего пользователя
        if self.original_username and username_field.data.lower() == self.original_username.lower():
            return
        # Проверка на уникальность для нового имени или при добавлении
        user = User.query.filter(
            User.username.ilike(username_field.data)).first()  # ilike для регистронезависимого сравнения
        if user:
            raise ValidationError('Это имя пользователя уже занято. Пожалуйста, выберите другое.')

    def validate_email(self, email_field):
        # Если email не изменился, и мы редактируем существующего пользователя
        if self.original_email and email_field.data.lower() == self.original_email.lower():
            return
        # Проверка на уникальность для нового email или при добавлении
        user = User.query.filter(User.email.ilike(email_field.data)).first()  # ilike для регистронезависимого сравнения
        if user:
            raise ValidationError('Этот email уже используется. Пожалуйста, укажите другой.')


class OrganizationForm(FlaskForm):
    name = StringField('Название организации',
                       validators=[
                           DataRequired(message="Обязательно введите название"),
                           Length(max=200, message="Максимальное количество символов: 200")
                       ],
                       filters=(names_fix,))

    inn = StringField('ИНН',
                      validators=[
                          DataRequired(message="Обязательно введите ИНН"),
                          Length(min=10, max=12, message="ИНН должен содержать от 10 до 12 цифр")  # Уточнено сообщение
                      ],
                      filters=(elmk_snils_fix,))

    address = StringField('Адрес',
                          validators=[
                              Optional(),
                              Length(max=200, message="Максимальное количество символов: 200")],
                          filters=(address_names_fix,))

    phone_number = StringField('Номер телефона', validators=[
        Optional(),
        Length(max=20, message="Максимальное количество символов: 20")
    ],
                               filters=(phone_number_fix,))

    email = StringField('Email', validators=[
        Optional(),
        Email(message="Некорректный адрес электронной почты"),
        Length(max=120, message="Максимальное количество символов: 120")
    ])

    is_active = BooleanField('Организация активна?', default=True)

    # Если поле 'info' из CrudInfoModel, убедитесь, что оно доступно
    # или добавьте его сюда, если оно должно быть редактируемым через форму
    # Например, если CrudInfoModel добавляет поле info:
    info = TextAreaField('Дополнительная информация', validators=[Optional()])

    submit = SubmitField(
        'Сохранить')  # Кнопка submit не используется в AJAX форме модалки, но нужна для стандартной формы

    # Добавляем параметр original_org_id для режима редактирования
    def __init__(self,
                 formdata=None,
                 obj=None,
                 prefix='',
                 meta=None, *,
                 original_org_id=None,
                 **kwargs):
        # Исправлено: аргументы передаются по имени
        super().__init__(formdata=formdata,
                         obj=obj,
                         prefix=prefix,
                         meta=meta,
                         **kwargs)
        self.original_org_id = original_org_id

    # Переопределяем валидацию INN для учета режима редактирования
    def validate_inn(self, field):

        if field.data:  # Проверяем уникальность только если ИНН введен
            inn_data = str(field.data).strip()

            # Этот базовый формат уже проверяется валидатором @validates в модели,
            # но повторная проверка здесь дает более быструю обратную связь пользователю на уровне формы.
            # Если вы доверяете валидатору модели, эту часть можно убрать,
            # но тогда ошибка формата придет как 500 или другая ошибка из запроса API.
            if not (10 <= len(inn_data) <= 12) or not inn_data.isdigit():
                raise ValidationError("ИНН должен содержать от 10 до 12 цифр.")

            # Проверка уникальности
            query = Organization.query.filter_by(inn=inn_data)

            # Если форма используется для редактирования (передан original_org_id),
            # исключаем текущую организацию из проверки на уникальность
            if self.original_org_id is not None:
                query = query.filter(Organization.id != self.original_org_id)

            organization = query.first()
            if organization:
                # Ошибка уникальности
                raise ValidationError("Организация с указанным ИНН уже зарегистрирована.")


def active_contracts_factory():
    # Можно добавить фильтр, например, только активные или не истекшие контракты
    return Contract.query.order_by(Contract.number).all()


class ContractForm(FlaskForm):
    number = StringField('Номер договора', validators=[InputRequired()])
    contract_date = DateField('Дата подписания', format='%Y-%m-%d', validators=[InputRequired()])
    name = StringField('Название договора')
    expiration_date = DateField('Срок окончания', format='%Y-%m-%d')
    is_extended = BooleanField('Продлён')
    info = TextAreaField('Дополнительная информация')
    # vizit_id = SelectField('Визит', coerce=int, choices=[])  # Новое поле
    organization_id = SelectField('Организация', coerce=int, choices=[])
    submit = SubmitField('Сохранить')

    def __init__(self, *args, **kwargs):
        super(ContractForm, self).__init__(*args, **kwargs)
        if Organization:  # Проверяем, что Organization была импортирована
            self.organization_id.choices = [(org.id, org.name) for org in
                                            Organization.query.order_by(Organization.name).all()]
        else:
            self.organization_id.choices = []  # Если импорт не удался, оставить пустым

    def check_duplicates(self):
        # Проверка на дубликаты
        existing_contract = Contract.query.filter_by(
            number=self.number.data,
            contract_date=self.contract_date.data,
            organization_id=self.organization_id.data
        ).first()

        if existing_contract:
            raise ValidationError(
                'Договор уже добавлен в БД. Пожалуйста, попробуйте внести другой номер, дату подписания или организацию.')
        return True


class VizitForm(FlaskForm):
    contingent_id = SelectField('Контингент', coerce=int, validators=[DataRequired()])
    attestation_type_id = SelectField('Тип аттестации', coerce=int, validators=[DataRequired()])
    work_field_id = SelectField('Сфера деятельности', coerce=int, validators=[DataRequired()])
    applicant_type_id = SelectField('Тип заявителя', coerce=int, validators=[DataRequired()])
    visit_date = DateField('Дата визита', validators=[DataRequired()])
    info = TextAreaField('Дополнительная информация',
                         validators=[
                             Optional(),
                             Length(max=300, message="Максимальное количество символов: 300")])
    contract = QuerySelectField(
        'Выберите контракт',
        query_factory=lambda: Contract.query.all(),  # Получаем все контракты
        get_label='show_info',  # Это поле будет отображаться в форме
        allow_blank=True,
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
    form_name = StringField(default='applicant_search_form', validators=[DataRequired()])
    last_name = StringField('Фамилия',
                            validators=[Optional()],
                            filters=(names_fix,))
    last_name_exact = BooleanField('Точное совпадение фамилии', default=False)  # Для полного совпадения
    snils_number = StringField('СНИЛС',
                               validators=[Optional(),
                                           Length(min=11, max=11, message="СНИЛС должен содержать 11 цифр."),
                                           Regexp(r'^\d+$', message="СНИЛС должен содержать только цифры")])
    medbook_number = StringField('Номер медицинской книжки',
                                 validators=[
                                     validators.Optional(),
                                     validators.Length(max=12),
                                     validators.Regexp(r'^[0-9]*$', message="ВВОДИТЕ ТОЛЬКО ЦИФРЫ!!!")
                                 ])
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
    updated_by_user = SelectField('Кем изменено последний раз', coerce=int, choices=[],
                                  validators=[Optional()])  # Поле для выбора пользователя
    updated_at_start = DateField('Дата последнего изменения (от)', format='%Y-%m-%d', validators=[Optional()])
    updated_at_end = DateField('Дата последнего изменения (до)', format='%Y-%m-%d', validators=[Optional()])
    search_submit = SubmitField('Найти заявителей')


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
    info = TextAreaField('Дополнительная информация',
                         validators=[
                             Optional(),
                             Length(max=300, message="Максимальное количество символов: 300")])
    submit = SubmitField('Сохранить')


class AccessSettingForm(FlaskForm):
    """
    Форма для создания и редактирования настроек программы AccessSetting.
    """
    name = StringField('Название настройки',
                       validators=[DataRequired(), Length(min=3, max=50,
                                                          message="Название должно быть от 3 до 50 символов.")])

    page_lock_seconds = IntegerField('Время блокировки страниц (сек)', validators=[
        DataRequired(message="Обязательное поле."),
        NumberRange(min=30, max=600, message="Значение должно быть от 30 до 600 секунд.")
    ])

    activity_timeout_seconds = IntegerField('Время простоя пользователя (сек)', validators=[
        DataRequired(message="Обязательное поле."),
        NumberRange(min=60, max=900, message="Значение должно быть от 60 до 900 секунд.")
    ])

    max_admins_number = IntegerField('Макс. число администраторов', validators=[
        DataRequired(message="Обязательное поле."),
        NumberRange(min=1, message="Значение не может быть менее 1.")
    ])

    max_moders_number = IntegerField('Макс. число модераторов', validators=[
        DataRequired(message="Обязательное поле."),
        NumberRange(min=1, message="Значение не может быть менее 1.")
    ])

    activity_period_counter = IntegerField('Периодичность проверки активности (клики)', validators=[
        DataRequired(message="Обязательное поле."),
        NumberRange(min=5, max=100, message="Значение должно быть от 5 до 100 кликов.")
    ])

    activity_counter_max_threshold = IntegerField('Периодичность обновления сессий (клики)', validators=[
        DataRequired(message="Обязательное поле."),
        NumberRange(min=10, max=10000, message="Значение должно быть от 10 до 10000 кликов.")
    ])

    submit = SubmitField('Сохранить')

    # Пользовательский валидатор для проверки зависимости между полями
    def validate_activity_counter_max_threshold(self, field):
        if self.activity_period_counter.data is not None and field.data is not None:
            if field.data < self.activity_period_counter.data:
                raise ValidationError(
                    "Периодичность обновления сессий не может быть меньше периодичности проверки активности.")

    def validate_activity_timeout_seconds(self, field):
        if self.page_lock_seconds.data is not None and field.data is not None:
            if field.data < self.page_lock_seconds.data:
                raise ValidationError(
                    "Время простоя пользователя "
                    "не может быть меньше времени блокировки страниц редактирования.")


class EditVisitForm(FlaskForm):
    # Поля, напрямую соответствующие колонкам в модели Visit
    visit_date = DateField('Дата визита', format='%Y-%m-%d', validators=[DataRequired()])
    info = TextAreaField('Дополнительная информация',
                         validators=[
                             Optional(),
                             Length(max=300, message="Максимальное количество символов: 300")])

    # SelectField для Foreign Key ID (как у вас в VizitForm)
    contingent_id = SelectField('Контингент', coerce=int, validators=[DataRequired()])
    attestation_type_id = SelectField('Тип аттестации', coerce=int, validators=[DataRequired()])
    work_field_id = SelectField('Сфера деятельности', coerce=int, validators=[DataRequired()])
    applicant_type_id = SelectField('Тип заявителя', coerce=int, validators=[DataRequired()])

    # QuerySelectField для Contract (как у вас в VizitForm)
    # Важно: QuerySelectField ожидает, что `visit.contract` будет объектом Contract,
    # а не `contract_id`. Если ваша модель Visit имеет связь `contract`, то это сработает.
    contract = QuerySelectField(
        'Выберите контракт',
        query_factory=lambda: Contract.query.all(),
        get_label='show_info',  # Метод или атрибут вашей модели Contract, который возвращает отображаемое имя
        allow_blank=True,
        blank_text='-- Не выбрано --',
        validators=[Optional()]
    )

    submit = SubmitField('Сохранить изменения')  # Имя кнопки для редактирования

    def __init__(self, *args, **kwargs):
        super(EditVisitForm, self).__init__(*args, **kwargs)
        # Динамическое заполнение вариантов для SelectField
        self.contingent_id.choices = [(c.id, c.name) for c in Contingent.query.order_by(Contingent.name).all()]
        self.attestation_type_id.choices = [(a.id, a.name) for a in
                                            AttestationType.query.order_by(AttestationType.name).all()]
        self.work_field_id.choices = [(w.id, w.name) for w in WorkField.query.order_by(WorkField.name).all()]
        self.applicant_type_id.choices = [(a.id, a.name) for a in
                                          ApplicantType.query.order_by(ApplicantType.name).all()]

        # QuerySelectField `contract` будет автоматически заполнен, если вы передадите `obj=visit`
        # и у вашей модели Visit есть атрибут `contract`, который является объектом Contract.
        # Если ваша модель Visit хранит только `contract_id`, то вам, возможно, придется
        # изменить тип поля `contract` на `SelectField` и вручную заполнять его `choices`.
        # Но если есть relationship, QuerySelectField - более элегантное решение.


# Если вы хотите валидировать существование директории на уровне формы,
# а не только модели, добавьте эту функцию:
def validate_directory_exists_form(form, field):
    if field.data:  # Проверяем, только если поле не пустое
        if not os.path.isdir(field.data.strip()):
            raise ValidationError(f"Директория '{field.data}' не существует.")


class BackupSettingForm(FlaskForm):
    name = StringField('Название настройки', validators=[DataRequired(), Length(max=100)])
    period_secs = IntegerField('Периодичность бэкапа (секунды)',
                               validators=[DataRequired(), NumberRange(min=300, max=86400 * 3)])
    check_period_secs = IntegerField('Таймаут между проверками (секунды)',
                                     validators=[DataRequired(), NumberRange(min=90, max=3600 * 3)])
    check_times = IntegerField('Количество проверок возможности бэкапа',
                               validators=[DataRequired(), NumberRange(min=1, max=10)])

    backup_local_dir = StringField('Локальная директория бэкапа',
                                   validators=[Optional(), validate_directory_exists_form, Length(max=255)])
    backup_lan_dir = StringField('Сетевая директория бэкапа (LAN)',
                                 validators=[Optional(), validate_directory_exists_form, Length(max=255)])

    # is_active_now не будет полем формы для ввода, оно будет управляться
    # отдельной кнопкой/радиокнопкой на HTML-странице.

    lifespan_days = IntegerField('Период хранения бэкапов (дней)',
                                 validators=[DataRequired(message="Период хранения обязателен."),
                                             NumberRange(min=7, max=30, message="Период должен быть от 7 до 30 дней.")])

    submit = SubmitField('Сохранить настройку')

    # Дополнительная валидация на уровне формы для сложных зависимостей полей
    def validate_check_times(self, field):
        if self.period_secs.data is not None and self.check_period_secs.data is not None and field.data is not None:
            period_secs_half = self.period_secs.data // 2
            if field.data * self.check_period_secs.data > period_secs_half:
                raise ValidationError("Произведение количества чекаутов на продолжительность таймаута "
                                      "между проверками возможности бэкапа "
                                      f"не может быть более ПОЛОВИНЫ ({period_secs_half} (округл. до целого числа)) "
                                      f"от значения периодичности бэкапа ({self.period_secs.data}) секунд.")
