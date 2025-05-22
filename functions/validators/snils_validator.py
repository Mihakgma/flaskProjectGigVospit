from wtforms.validators import ValidationError
from flask_wtf import FlaskForm

from models import Applicant


def validate_snils(form: FlaskForm, field):
    if not field.data:
        raise ValidationError('ПОЖАЛУЙСТА ВВЕДИТЕ НОМЕР СНИЛС!!!')

    numbers = [i for i in field.data if i.isnumeric()]
    if len(numbers) != 11:
        raise ValidationError('Неверный формат СНИЛС. Требуется 11 цифр.')

    # Проверка дубликатов
    current_applicant = getattr(form, '_obj', None)
    existing = Applicant.query.filter(
        Applicant.snils_number == field.data
    ).first()

    # Если запись найдена И (это новая запись ИЛИ это другая существующая запись)
    if not current_applicant:
        pass
    elif existing and existing.id == current_applicant.id:
        pass
    elif existing and (not current_applicant or existing.id != current_applicant.id):
        raise ValidationError(f'СНИЛС уже используется: {existing.full_name}')


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