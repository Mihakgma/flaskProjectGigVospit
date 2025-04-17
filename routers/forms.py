from wtforms import (Form,
                     StringField,
                     SelectField,
                     SubmitField,
                     BooleanField,
                     DateField,
                     TextAreaField)
from wtforms.validators import DataRequired, Length, Email, Optional


class AddApplicantForm(Form):
    first_name = StringField('Имя', validators=[DataRequired(), Length(max=80)])
    last_name = StringField('Фамилия', validators=[DataRequired(), Length(max=80)])
    middle_name = StringField('Отчество', validators=[Length(max=80)])
    medbook_number = StringField('Номер медицинской книжки', validators=[Length(max=50)])
    snils_number = StringField('СНИЛС', validators=[Length(max=14)])
    passport_number = StringField('Номер паспорта', validators=[Length(max=20)])
    birth_date = DateField('Дата рождения', format='%Y-%m-%d', validators=[DataRequired()])  # DateField для даты
    registration_address = StringField('Адрес регистрации', validators=[Length(max=200)])
    residence_address = StringField('Адрес проживания', validators=[Length(max=200)])
    phone_number = StringField('Телефон', validators=[Length(max=20)])  # Используем StringField
    email = StringField('Email', validators=[Optional(), Email(), Length(max=120)])  # Используем StringField
    contingent_id = SelectField('Контингент', coerce=int, validators=[DataRequired()])
    work_field_id = SelectField('Сфера деятельности', coerce=int, validators=[DataRequired()])
    applicant_type_id = SelectField('Тип заявителя', coerce=int, validators=[DataRequired()])
    attestation_type_id = SelectField('Тип аттестации', coerce=int, validators=[DataRequired()])
    edited_by_user_id = SelectField('Редактировал (ID пользователя)', coerce=int, validators=[DataRequired()])
    is_editing_now = BooleanField('Редактируется сейчас')
    editing_by_id = SelectField('Редактирует сейчас (ID пользователя)', coerce=int)
    submit = SubmitField('Добавить заявителя')


class AddContractForm(Form):
    number = StringField('Номер контракта', validators=[DataRequired(), Length(max=50)])
    contract_date = DateField('Дата заключения', format='%Y-%m-%d', validators=[DataRequired()])
    name = TextAreaField('Название контракта', validators=[DataRequired()])
    expiration_date = DateField('Дата истечения', format='%Y-%m-%d', validators=[Optional()])
    is_extended = BooleanField('Продлен')
    organization_id = SelectField('Организация', coerce=int, validators=[DataRequired()])
    additional_info = TextAreaField('Дополнительная информация')
    submit = SubmitField('Добавить контракт')
