from wtforms.validators import ValidationError
from flask_wtf import FlaskForm

from models import Applicant


def validate_med_book(form: FlaskForm, field):
    if not field.data:
        raise ValidationError('ПОЖАЛУЙСТА ВВЕДИТЕ НОМЕР МЕД КНИЖКИ!!!')

    numbers = [i for i in field.data if i.isnumeric()]
    if len(numbers) != 12:
        raise ValidationError('Неверный формат. Требуется 12 цифр.')

    current_applicant = getattr(form, '_obj', None)
    existing = Applicant.query.filter(
        Applicant.medbook_number == field.data
    ).first()

    if not current_applicant:
        pass
    elif existing and existing.id == current_applicant.id:
        pass
    elif existing and (not current_applicant or existing.id != current_applicant.id):
        raise ValidationError(f'Мед. книжка уже используется: {existing.full_name}')


if __name__ == '__main__':
    med_book_numbers = ["12-01-",
                        "42-01-022472-24",
                        "42-01.022472|24^%&^",
                        "@%&^#()*!@_+=42-01-022472-25",
                        "",
                        "42-01-024624-25",
                        "420102462425"]
    for number in med_book_numbers:
        try:
            validate_med_book(FlaskForm, number)
        except ValidationError as e:
            # print(e)
            print(f"Ошибка по номеру книжки: <{number}>")
