from datetime import date
from wtforms.validators import ValidationError
from flask_wtf import FlaskForm


# Кастомный валидатор
def validate_birth_date(form: FlaskForm, field):
    """Проверяем, что дата рождения не позже сегодняшнего дня."""
    input_date = field.data
    if input_date >= date.today():
        raise ValidationError("Дата рождения не должна быть из будущего.")
