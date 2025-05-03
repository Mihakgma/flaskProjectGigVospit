from datetime import date, datetime
from wtforms.validators import ValidationError
from flask_wtf import FlaskForm


def validate_birth_date(form: FlaskForm, field):
    input_date = field.data
    today = date.today()
    if isinstance(input_date, datetime):
        input_date = input_date.date()
    dates_difference = today - input_date
    dates_difference_years = round(dates_difference.days / 365.25, 0)
    dates_difference_months = abs(today.month - input_date.month)
    if input_date >= today:
        raise ValidationError("Дата рождения не должна быть из будущего.")
    elif input_date < today and dates_difference_years < 14:
        raise ValidationError(f"Заявителю должно быть как минимум 14 лет, "
                              f"фактич. возраст ~ <{dates_difference_years}> лет, <{dates_difference_months}> мес.")
    elif input_date < today and dates_difference_years > 90:
        raise ValidationError(f"Заявителю пора на заслуженный отдых, "
                              f"фактич. возраст ~ <{dates_difference_years}> лет, <{dates_difference_months}> мес.")
