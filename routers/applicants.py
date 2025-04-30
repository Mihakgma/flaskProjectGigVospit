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

from datetime import timezone

from forms.forms import (AddApplicantForm,
                         VizitForm, ApplicantSearchForm)
from sqlalchemy import or_, and_
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
@role_required('anyone')  # Или укажите нужную роль
def search_applicants():
    form = ApplicantSearchForm()
    applicants = []

    if request.method == 'POST' and form.validate_on_submit():
        search_criteria = {}
        if not any(field.data for field in form if field.name not in ['csrf_token', 'submit', 'last_name_exact']):
            flash('Заполните хотя бы одно поле для поиска', 'error')
            return render_template('search_applicants.html', form=form, applicants=applicants)

        if form.last_name.data and len(form.last_name.data) < 2:
            flash('Фамилия должна содержать не менее 2 символов', 'error')
            return render_template('search_applicants.html', form=form, applicants=applicants)

        if (form.registration_address.data and len(form.registration_address.data) < 2) or \
                (form.residence_address.data and len(form.residence_address.data) < 2):
            flash('Адрес должен содержать не менее 2 символов', 'error')
            return render_template('search_applicants.html', form=form, applicants=applicants)

        if form.birth_date_start.data and form.birth_date_end.data is None:
            flash('Заполните конечную дату рождения', 'error')
            return render_template('search_applicants.html', form=form, applicants=applicants)

        if form.last_visit_start.data and form.last_visit_end.data is None:
            flash('Заполните конечную дату последнего визита', 'error')
            return render_template('search_applicants.html', form=form, applicants=applicants)

        if form.last_name.data:
            search_criteria['last_name'] = func.lower(form.last_name.data).strip()  # Добавляем lower() и strip()

        if form.registration_address.data:
            search_criteria['registration_address'] = func.lower(
                form.registration_address.data).strip()  # Добавляем lower() и strip()

        if form.residence_address.data:
            search_criteria['residence_address'] = func.lower(
                form.residence_address.data).strip()  # Добавляем lower() и strip()

        if 'snils_part1' in request.form:
            snils_parts = [request.form.get(f'snils_part{i}') for i in range(1, 5)]
            snils = ''.join(filter(None, snils_parts))  # Объединяем части СНИЛС, удаляя пустые строки
            if snils:  # Если СНИЛС введен
                search_criteria['snils_number'] = int(snils)

        if 'medbook_part1' in request.form:
            medbook_parts = [request.form.get(f'medbook_part{i}') for i in range(1, 5)]
            medbook = ''.join(filter(None, medbook_parts))  # Объединяем части номера медкнижки
            if medbook:
                search_criteria['medbook_number'] = int(medbook)

        search_criteria = {}

        if form.last_name.data:
            if form.last_name_exact.data:  # Полное совпадение
                search_criteria['last_name'] = form.last_name.data
            else:  # Частичное совпадение
                search_criteria['last_name'] = {'like': f'%{form.last_name.data}%'}

        if form.snils_number.data:
            search_criteria['snils_number'] = form.snils_number.data

        if form.medbook_number.data:
            search_criteria['medbook_number'] = form.medbook_number.data

        if form.birth_date_start.data:
            search_criteria['birth_date'] = {'gte': form.birth_date_start.data}
        if form.birth_date_end.data:
            search_criteria.setdefault('birth_date', {}).update({'lte': form.birth_date_end.data})

        if form.last_visit_start.data or form.last_visit_end.data:
            subquery = Vizit.query.with_entities(Vizit.applicant_id,
                                                 db.func.max(Vizit.created_at).label('last_visit')).group_by(
                Vizit.applicant_id).subquery()

            filters = []
            for field_name, value in search_criteria.items():
                if field_name == 'last_name':
                    filters.append(func.upper(Applicant.last_name).contains(value))  # contains + lower() для фамилии
                elif field_name == 'registration_address':
                    filters.append(func.lower(Applicant.registration_address).contains(
                        value))  # contains + lower() для адреса регистрации
                elif field_name == 'residence_address':
                    filters.append(func.lower(Applicant.residence_address).contains(
                        value))  # contains + lower() для адреса проживания
                elif field_name == 'last_name_exact':
                    filters.append(func.lower(Applicant.last_name) == value)
                else:
                    filters.append(getattr(Applicant, field_name) == value)
            if form.last_visit_start.data:
                filters.append(subquery.c.last_visit >= form.last_visit_start.data)
            if form.last_visit_end.data:
                filters.append(subquery.c.last_visit <= form.last_visit_end.data)

            applicant_ids = db.session.query(subquery.c.applicant_id).filter(and_(*filters)).all()
            search_criteria['id'] = {'in_': [id[0] for id in applicant_ids]}

        if form.registration_address.data:
            search_criteria['registration_address'] = {'like': f'%{form.registration_address.data}%'}

        if form.residence_address.data:
            search_criteria['residence_address'] = {'like': f'%{form.residence_address.data}%'}

        query = Applicant.query
        for field, value in search_criteria.items():
            if isinstance(value, dict):  # Для like, gte, lte, in_
                if 'like' in value:
                    query = query.filter(getattr(Applicant, field).like(value['like']))
                elif 'gte' in value:
                    query = query.filter(getattr(Applicant, field) >= value['gte'])
                elif 'lte' in value:
                    query = query.filter(getattr(Applicant, field) <= value['lte'])
                elif 'in_' in value:
                    query = query.filter(getattr(Applicant, field).in_(value['in_']))

            else:
                query = query.filter(getattr(Applicant, field) == value)

        applicants = query.all()

    return render_template('search_applicants.html', form=form, applicants=applicants)
