from wtforms.validators import ValidationError
from flask_wtf import FlaskForm


def validate_snils(form: FlaskForm, field):
    if type(field) is str:
        number_in = field
    elif not field.data:
        raise ValidationError('ПОЖАЛУЙСТА ВВЕДИТЕ НОМЕР СНИЛС!!!')
    else:
        number_in = field.data
    numbers = [i for i in number_in if i.isnumeric()]
    if len(numbers) != 11:
        raise ValidationError('Требуемый формат для номера СНИЛС: '
                              'ХХХ-ХХХ-ХХХ-ХХ, ХХХ-ХХХ-ХХХ ХХ или '
                              'ХХХХХХХХХХХ')


if __name__ == '__main__':
    snils_numbers = ["12-01-",
                     "299-715-524-90",
                     "42-01.022472|4^%&^",
                     "@%&^#()*!@_+=876_341_900_00",
                     "",
                     "42-01-024624-25",
                     "12312345678"]
    for number in snils_numbers:
        try:
            validate_snils(FlaskForm, number)
        except ValidationError as e:
            # print(e)
            print(f"Ошибка по номеру СНИЛС: <{number}>")