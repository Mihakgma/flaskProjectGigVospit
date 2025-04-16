from wtforms import Form, StringField, SelectField, SubmitField
from wtforms.validators import DataRequired, Length


class AddApplicantForm(Form):
    first_name = StringField('Имя', validators=[DataRequired(), Length(max=100)])
    last_name = StringField('Фамилия', validators=[DataRequired(), Length(max=100)])
    middle_name = StringField('Отчество', validators=[Length(max=100)])
    # Остальные поля формы...
    submit = SubmitField('Добавить заявителя')
