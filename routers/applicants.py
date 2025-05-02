from flask import (Blueprint,
                   render_template,
                   request,
                   redirect,
                   url_for,
                   flash)
from flask_login import login_required

from functions.access_control import role_required
from models.models import (Applicant,
                           Vizit)
from database import db

from datetime import timezone, date, datetime

from forms.forms import (AddApplicantForm,
                         VizitForm, ApplicantSearchForm)
from sqlalchemy import and_
from sqlalchemy.sql.expression import func

applicants_bp = Blueprint('applicants', __name__)  # Создаем blueprint


@applicants_bp.route('/add', methods=['GET', 'POST'])
@login_required
@role_required('admin', 'moder', 'oper', )
def add_applicant():
    applicant_form = AddApplicantForm()
    vizit_form = VizitForm()

    if request.method == 'POST':
        if applicant_form.validate_on_submit():  # Валидация формы заявителя
            try:
                new_applicant = Applicant()
                applicant_form.populate_obj(new_applicant)
                db.session.add(new_applicant)
                db.session.flush()

                if vizit_form.validate_on_submit():  # Валидация формы визита
                    new_vizit = Vizit()
                    vizit_form.populate_obj(new_vizit)
                    new_vizit.applicant_id = new_applicant.id
                    new_vizit.created_at = vizit_form.created_at.data
                    db.session.add(new_vizit)
                    new_applicant.vizits.append(new_vizit)

                db.session.commit()
                flash('Заявитель и визит (если был добавлен) успешно сохранены!', 'success')
                return redirect(url_for('applicants.applicant_details',
                                        applicant_id=new_applicant.id))

            except Exception as e:
                db.session.rollback()
                print(f"Ошибка при добавлении заявителя/визита: {e}")
                flash('Произошла ошибка при добавлении. Попробуйте позже.', 'danger')

        else:  # Если форма заявителя не валидна, проверяем и добавляем визит отдельно, если валиден
            if vizit_form.validate_on_submit():
                flash('Форма заявителя содержит ошибки. Пожалуйста исправьте их.', 'danger')

        # Выводим ошибки валидации формы заявителя, если они есть
        for field, errors in applicant_form.errors.items():
            for error in errors:
                flash(f"Ошибка в поле '{applicant_form[field].label.text}': {error}", 'danger')

    return render_template('add_applicant.html',
                           form=applicant_form,
                           vizit_form=vizit_form)


@applicants_bp.route('/details/<int:applicant_id>')
@login_required
@role_required('anyone')
def applicant_details(applicant_id):
    applicant = Applicant.query.get_or_404(applicant_id)
    return render_template('applicant_details.html',
                           applicant=applicant,
                           timezone=timezone)


@applicants_bp.route('/search_applicants', methods=['GET', 'POST'])
@login_required
@role_required('anyone')
def search_applicants():
    form = ApplicantSearchForm(request.args)
    page = int(request.args.get('page', 1))
    per_page = int(request.args.get('per_page', 20))

    filters = []

    last_visit_sq = (  # Объявляем подзапрос ДО цикла
        db.session.query(
            Vizit.applicant_id,
            func.max(Vizit.created_at).label('last_visit_date')
        )
        .group_by(Vizit.applicant_id)
        .subquery()
    )

    query = db.session.query(Applicant).outerjoin(
        last_visit_sq, Applicant.id == last_visit_sq.c.applicant_id
    )

    for field_name, value in request.args.items():
        if value and field_name not in ('page', 'per_page', 'submit'):
            if field_name in ('birth_date_start', 'birth_date_end', 'last_visit_start', 'last_visit_end'):
                try:
                    value = date.fromisoformat(value)
                    # Проверяем корректность даты
                    assert isinstance(value, datetime.date), f'Некорректная дата: {value}'

                    if field_name == 'birth_date_start':
                        filters.append(Applicant.birth_date >= value)
                    elif field_name == 'birth_date_end':
                        filters.append(Applicant.birth_date <= value)
                    elif field_name == 'last_visit_start':
                        filters.append(last_visit_sq.c.last_visit_date >= value)
                    elif field_name == 'last_visit_end':
                        filters.append(last_visit_sq.c.last_visit_date <= value)

                except (ValueError, AssertionError):
                    flash("Ошибка в формате даты!", "error")
                    return redirect(url_for('applicants.search_applicants'))
            elif field_name.startswith(('snils_part', 'medbook_part')):
                parts = [request.args.get(f'{field_name[:-1]}{i}') for i in range(1, 5)]
                valid_parts = list(filter(lambda x: len(x.strip()) > 0, parts))  # Убираем пустые части
                if valid_parts:
                    try:
                        full_number = ''.join(valid_parts)
                        filters.append(getattr(Applicant, field_name[:-7] + '_number') == int(full_number))
                    except ValueError:
                        flash(f"Неверный формат {field_name[:-7].replace('_', ' ').title()}", "error")
                        return redirect(url_for('applicants.search_applicants'))

            # Для всех остальных полей
            else:
                try:
                    filters.append(getattr(Applicant, field_name) == value)
                except AttributeError:
                    print(f"Warning: Unknown field '{field_name}'")  # Логирование неизвестных полей

    if not filters:
        query = db.session.query(Applicant).outerjoin(
            last_visit_sq, Applicant.id == last_visit_sq.c.applicant_id
        )  # Запрос без фильтров, если filters пуст
    else:
        query = query.filter(and_(*filters))

    print(query)

    url_args = request.args.copy()
    url_args.pop('page', None)
    url_args.pop('per_page', None)

    total_count = query.count()
    applicants = query.paginate(page=page, per_page=per_page, error_out=False)

    return render_template(
        'search_applicants.html',
        form=form,
        applicants=applicants,
        total_count=total_count,
        per_page=per_page,
        url_args=url_args  # Передаем url_args в шаблон
    )
