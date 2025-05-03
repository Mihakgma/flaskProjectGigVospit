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
    form = ApplicantSearchForm()
    applicants = []

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

    if request.method == 'POST' and form.validate_on_submit():
        search_criteria = {}

        if not any(field.data for field in form if field.name not in ['csrf_token', 'submit', 'last_name_exact']) and \
                not ('snils_part1' in request.form or 'medbook_part1' in request.form):
            flash('Заполните хотя бы одно поле для поиска', 'error')
            return render_template('search_applicants.html', form=form, applicants=applicants)

        if form.last_name.data:
            if len(form.last_name.data) < 2:
                flash('Фамилия должна содержать не менее 2 символов', 'error')
                return render_template('search_applicants.html', form=form, applicants=applicants)
            search_criteria['last_name'] = form.last_name.data

        if form.registration_address.data:
            if len(form.registration_address.data) < 2:
                flash('Адрес регистрации должен содержать не менее 2 символов', 'error')
                return render_template('search_applicants.html', form=form, applicants=applicants)
            search_criteria['registration_address'] = form.registration_address.data

        if form.residence_address.data:
            if len(form.residence_address.data) < 2:
                flash('Адрес проживания должен содержать не менее 2 символов', 'error')
                return render_template('search_applicants.html', form=form, applicants=applicants)
            search_criteria['residence_address'] = form.residence_address.data

        if 'snils_part1' in request.form:
            snils_parts = [request.form.get(f'snils_part{i}') for i in range(1, 5)]
            snils = ''.join(filter(None, snils_parts))
            if snils:
                try:
                    search_criteria['snils_number'] = int(snils)
                except ValueError:
                    flash('СНИЛС должен содержать только цифры', 'error')
                    return render_template('search_applicants.html', form=form, applicants=applicants)

        if 'medbook_part1' in request.form:
            medbook_parts = [request.form.get(f'medbook_part{i}') for i in range(1, 5)]
            medbook = ''.join(filter(None, medbook_parts))
            if medbook:
                try:
                    search_criteria['medbook_number'] = int(medbook)
                except ValueError:
                    flash('Номер медкнижки должен содержать только цифры', 'error')
                    return render_template('search_applicants.html', form=form, applicants=applicants)

        if form.birth_date_start.data and form.birth_date_end.data is None:
            flash('Заполните конечную дату рождения', 'error')
            return render_template('search_applicants.html', form=form, applicants=applicants)

        if form.last_visit_start.data and form.last_visit_end.data is None:
            flash('Заполните конечную дату последнего визита', 'error')
            return render_template('search_applicants.html', form=form, applicants=applicants)

        if form.birth_date_start.data:
            search_criteria['birth_date_start'] = form.birth_date_start.data
        if form.birth_date_end.data:
            search_criteria['birth_date_end'] = form.birth_date_end.data

        if form.last_visit_start.data:
            search_criteria['last_visit_start'] = form.last_visit_start.data
        if form.last_visit_end.data:
            search_criteria['last_visit_end'] = form.last_visit_end.data

        filters = []
        for field_name, value in search_criteria.items():
            if field_name == 'last_name':
                filters.append(func.upper(getattr(Applicant, field_name)).contains(value))
            elif field_name == 'last_name_exact':
                filters.append(func.lower(getattr(Applicant, field_name[0:-6])) == value)
            elif field_name in ['registration_address', 'residence_address']:
                filters.append(getattr(Applicant, field_name).contains(value))
            elif field_name in ['snils_number', 'medbook_number']:
                filters.append(getattr(Applicant, field_name) == value)
            elif field_name == 'birth_date_start':
                filters.append(Applicant.birth_date >= value)
            elif field_name == 'birth_date_end':
                filters.append(Applicant.birth_date <= value)
            elif field_name == 'last_visit_start':
                filters.append(last_visit_sq.c.last_visit_date >= value)
            elif field_name == 'last_visit_end':
                filters.append(last_visit_sq.c.last_visit_date <= value)
            else:
                filters.append(getattr(Applicant, field_name) == value)

        # Пример запроса:
        applicants = Applicant.query.filter(and_(*filters)).all()

    return render_template(
        'search_applicants.html',
        form=form,
        applicants=applicants
    )
