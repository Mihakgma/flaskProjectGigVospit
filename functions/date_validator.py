from datetime import date
from wtforms.validators import ValidationError
from wtforms import Form


# Кастомный валидатор
def validate_birth_date(form: Form, field):
    """Проверяем, что дата рождения не позже сегодняшнего дня."""
    input_date = field.data
    if input_date >= date.today():
        raise ValidationError("Дата рождения не должна быть из будущего.")
