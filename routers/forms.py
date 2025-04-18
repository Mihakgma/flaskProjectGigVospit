from flask_wtf import FlaskForm
from wtforms import (StringField,
                     SelectField,
                     SubmitField,
                     BooleanField,
                     DateField,
                     TextAreaField)
from wtforms.validators import DataRequired, Length, Email, Optional

from functions import validate_birth_date


class AddApplicantForm(FlaskForm):
    first_name = StringField('Имя', validators=[DataRequired(), Length(max=80)])
    # print('name ok')
    last_name = StringField('Фамилия', validators=[DataRequired(), Length(max=80)])
    # print('last name ok')
    middle_name = StringField('Отчество', validators=[Length(max=80)])
    # print('middle name ok')
    medbook_number = StringField('Номер медицинской книжки', validators=[Length(max=50)])
    # print('medbook_number ok')
    snils_number = StringField('СНИЛС', validators=[Length(max=14)])
    # print('snils_number ok')
    passport_number = StringField('Номер паспорта', validators=[Length(max=20)])
    # print('passport_number ok')
    birth_date = DateField(
        'Дата рождения',
        format='%Y-%m-%d',
        validators=[
            DataRequired(),
            validate_birth_date
        ]
    )
    # print('birth_date ok')
    registration_address = StringField('Адрес регистрации', validators=[Length(max=200)])
    # print('registration_address ok')
    residence_address = StringField('Адрес проживания', validators=[Length(max=200)])
    # print('residence_address ok')
    phone_number = StringField('Телефон', validators=[Length(max=20)])  # Используем StringField
    # print('phone_number ok')
    email = StringField('Email', validators=[Optional(), Email(), Length(max=120)])  # Используем StringField
    # print('email ok')
    contingent_id = SelectField('Контингент', coerce=int, validators=[DataRequired()])
    # print('contingent_id ok')
    work_field_id = SelectField('Сфера деятельности', coerce=int, validators=[DataRequired()])
    # print('work_field_id ok')
    applicant_type_id = SelectField('Тип заявителя', coerce=int, validators=[DataRequired()])
    # print('applicant_type_id ok')
    attestation_type_id = SelectField('Тип аттестации', coerce=int, validators=[DataRequired()])
    # print('attestation_type_id ok')
    edited_by_user_id = SelectField('Редактировал (ID пользователя)', coerce=int, validators=[DataRequired()])
    # print('edited_by_user_id ok')
    is_editing_now = BooleanField('Редактируется сейчас')
    # print('is_editing_now ok')
    editing_by_id = SelectField('Кто редактирует', coerce=int, validators=[Optional()])
    # print('editing_by_id ok')
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
