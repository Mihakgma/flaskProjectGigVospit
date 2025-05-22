from wtforms.validators import ValidationError
from flask_wtf import FlaskForm

from models import Applicant


def validate_med_book(form: FlaskForm, field):
    if type(field) is str:
        number_in = field
    elif not field.data:
        raise ValidationError('ПОЖАЛУЙСТА ВВЕДИТЕ НОМЕР МЕД КНИЖКИ!!!')
    else:
        number_in = field.data
    numbers = [i for i in number_in if i.isnumeric()]
    if len(numbers) != 12:
        raise ValidationError('Требуемый формат для номера мед. книжки: '
                              'ХХ-ХХ-ХХХХХХ-ХХ или '
                              'ХХХХХХХХХХХХ')
    # For edit forms, exclude current record
    applicant = getattr(form, '_obj', None)
    query = Applicant.query.filter_by(medbook_number=field.data)
    if applicant:
        query = query.filter(Applicant.id != applicant.id)
    q_first = query.first()
    if q_first:
        raise ValidationError('Медицинская книжка с таким номером уже существует '
                              f'ФИО <{q_first.last_name, q_first.first_name, q_first.middle_name}>')


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
