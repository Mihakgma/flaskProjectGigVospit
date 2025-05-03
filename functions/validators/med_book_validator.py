from wtforms.validators import ValidationError
from flask_wtf import FlaskForm


def validate_med_book(form: FlaskForm, field):
    if type(field) is str:
        number_in = field
    else:
        number_in = field.data
    numbers = [i for i in number_in if i.isnumeric()]
    if len(numbers) != 12:
        raise ValidationError('Требуемый формат для номера мед. книжки: '
                              'ХХ-ХХ-ХХХХХХ-ХХ или '
                              'ХХХХХХХХХХХХ')


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
