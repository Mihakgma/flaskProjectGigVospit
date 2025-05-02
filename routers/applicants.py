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

from datetime import timezone, datetime

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

    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)

    if request.method == 'POST' and form.validate_on_submit():
        search_criteria = request.form.to_dict()
        search_criteria.pop('csrf_token', None)
        search_criteria.pop('submit', None)
        if form.last_visit_start.data:
            search_criteria['last_visit_start'] = form.last_visit_start.data.isoformat()
        if form.last_visit_end.data:
            search_criteria['last_visit_end'] = form.last_visit_end.data.isoformat()
        return redirect(url_for('applicants.search_applicants', **search_criteria))

    search_criteria = request.args.to_dict()
    filters = []

    for field_name, value in search_criteria.items():
        # Исключаем 'page' и 'per_page' из обработки фильтров, а также пустые значения
        if field_name not in ('page', 'per_page') and value:
            if field_name == 'last_name':
                filters.append(func.upper(Applicant.last_name).contains(value.upper()))
            elif field_name == 'last_name_exact':
                filters.append(func.lower(Applicant.last_name) == value.lower())
            elif field_name in ['registration_address', 'residence_address']:
                filters.append(getattr(Applicant, field_name).contains(value))
            elif field_name.startswith('snils_part'):
                snils_parts = [search_criteria.get(f'snils_part{i}') for i in range(1, 5)]
                snils = ''.join(filter(None, snils_parts))
                if snils:
                    try:
                        filters.append(Applicant.snils_number == int(snils))
                    except ValueError:
                        pass  # Сообщение об ошибке
            elif field_name.startswith('medbook_part'):
                medbook_parts = [search_criteria.get(f'medbook_part{i}') for i in range(1, 5)]
                medbook = ''.join(filter(None, medbook_parts))
                if medbook:
                    try:
                        filters.append(Applicant.medbook_number == int(medbook))
                    except ValueError:
                        pass  # Сообщение об ошибке
            elif field_name == 'birth_date_start':
                filters.append(Applicant.birth_date >= datetime.fromisoformat(value))
            elif field_name == 'birth_date_end':
                filters.append(Applicant.birth_date <= datetime.fromisoformat(value))
            elif field_name == 'last_visit_start':
                # Нет direct поля last_visit, используем Vizit model
                subq = db.session.query(Vizit.applicant_id) \
                    .filter(Vizit.created_at >= datetime.fromisoformat(value)) \
                    .exists()
                filters.append(subq)
            elif field_name == 'last_visit_end':
                # Аналогичная ситуация с last_visit_end
                subq = db.session.query(Vizit.applicant_id) \
                    .filter(Vizit.created_at <= datetime.fromisoformat(value)) \
                    .exists()
                filters.append(subq)
            # Для всех остальных полей, если такие есть
            else:
                try:
                    filters.append(getattr(Applicant, field_name) == value)
                except AttributeError:
                    pass  # Игнорируем неизвестные поля

    query = Applicant.query.filter(and_(*filters))

    total_count = query.count()
    applicants = query.paginate(page=page, per_page=per_page, error_out=False)

    return render_template(
        'search_applicants.html',
        form=form,
        applicants=applicants,
        total_count=total_count,
        per_page=per_page
    )
