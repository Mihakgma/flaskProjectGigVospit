from datetime import date
from wtforms.validators import ValidationError
from flask_wtf import FlaskForm


# Кастомный валидатор
def validate_birth_date(form: FlaskForm, field):
    """Проверяем, что дата рождения не позже сегодняшнего дня."""
    input_date = field.data
    today = date.today()
    dates_difference = today - input_date
    dates_difference_years = round(dates_difference.days / 365.25, 0)
    dates_difference_months = today.month - input_date.month
    if dates_difference_months < 0:
        dates_difference_months = 0
    if input_date >= today:
        raise ValidationError("Дата рождения не должна быть из будущего.")
    elif input_date < today and dates_difference_years < 14:
        raise ValidationError(f"Заявителю должно быть как минимум 14 лет, "
                              f"фактич. ~ <{dates_difference_years}> лет, <{dates_difference_months}> мес.")
    elif input_date < today and dates_difference_years > 90:
        raise ValidationError(f"Заявителю пора на заслуженный отдых, "
                              f"фактич. ~ <{dates_difference_years}> лет, <{dates_difference_months}> мес.")
