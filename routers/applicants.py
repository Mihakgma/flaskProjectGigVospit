from io import BytesIO

import pandas as pd
from flask import (Blueprint,
                   render_template,
                   request,
                   redirect,
                   url_for,
                   flash, send_file)
from flask_login import login_required, current_user
from sqlalchemy.orm import joinedload

from functions import thread
from functions.access_control import role_required
from models.models import (Applicant,
                           Vizit, User, Contract)
from database import db

from datetime import timezone, datetime

from forms.forms import (AddApplicantForm,
                         VizitForm, ApplicantSearchForm, ApplicantEditForm)
from sqlalchemy import and_, event
from sqlalchemy.sql.expression import func

applicants_bp = Blueprint('applicants', __name__)


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
                    new_vizit.visit_date = vizit_form.visit_date.data
                    new_vizit.additional_info = vizit_form.additional_info.data
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
@role_required('admin', 'moder', 'oper', )
def applicant_details(applicant_id):
    applicant = Applicant.query.get_or_404(applicant_id)
    visits = Vizit.query.filter_by(applicant_id=applicant_id).all()
    for visit in visits:
        if not visit.contract:
            flash(f"Визит от {visit.visit_date} не прикреплен к контракту (договору).", category='warning')
    return render_template('applicant_details.html',
                           applicant=applicant,
                           visits=visits,
                           timezone=timezone)


@applicants_bp.route('/applicant/<int:applicant_id>/edit', methods=['GET', 'POST'])
@login_required
@role_required('admin', 'moder', 'oper')
def edit_applicant(applicant_id):
    applicant = Applicant.query.get_or_404(applicant_id)
    visits = Vizit.query.filter_by(applicant_id=applicant_id).all()
    applicant_form = ApplicantEditForm(obj=applicant)
    vizit_form = VizitForm()
    applicant.edited_time = datetime.utcnow()
    applicant.edited_by_user_id = current_user.id

    if request.method == 'POST':
        if applicant_form.submit.data and applicant_form.validate_on_submit():
            applicant_form.populate_obj(applicant)
            db.session.commit()
            flash('Данные заявителя обновлены', 'success')
            return redirect(url_for('applicants.edit_applicant', applicant_id=applicant.id))

        elif vizit_form.submit_visit.data and vizit_form.validate_on_submit():
            try:
                new_vizit = Vizit()
                vizit_form.populate_obj(new_vizit)
                new_vizit.applicant_id = applicant.id
                new_vizit.visit_date = vizit_form.visit_date.data
                new_vizit.additional_info = vizit_form.additional_info.data

                # Если выбран контракт, привязываем его
                if vizit_form.contract.data:
                    new_vizit.contract_id = vizit_form.contract.data.id  # Привязываем контракт к визиту

                db.session.add(new_vizit)
                applicant.vizits.append(new_vizit)  # Если используете relationship
                db.session.commit()
                flash('Визит добавлен', 'success')
                return redirect(url_for('applicants.edit_applicant', applicant_id=applicant.id))
            except Exception as e:
                db.session.rollback()
                print(f"Ошибка при добавлении визита: {e}")
                flash(f"Ошибка при добавлении визита: {e}", 'danger')

        # Выводим ошибки валидации формы заявителя, если они есть
        if not applicant_form.validate_on_submit():
            for field, errors in applicant_form.errors.items():
                for error in errors:
                    flash(f"Ошибка в поле '{applicant_form[field].label.text}': {error}", 'danger')

        if not vizit_form.validate_on_submit():
            for field, errors in vizit_form.errors.items():
                for error in errors:
                    flash(f"Ошибка в поле '{vizit_form[field].label.text}': {error}", 'danger')

        return redirect(url_for('applicants.edit_applicant', applicant_id=applicant.id))

    return render_template('edit_applicant.html',
                           applicant=applicant,
                           applicant_form=applicant_form,
                           visit_form=vizit_form,
                           visits=visits)


@applicants_bp.route('/search_applicants', methods=['GET', 'POST'])
@login_required
@role_required('anyone')
def search_applicants():
    form = ApplicantSearchForm(request.form)  # Используем request.form для POST
    applicants = []
    users = User.query.all()
    form.edited_by_user.choices = [(user.id, user.username) for user in users]
    form.edited_by_user.choices.insert(0, (0, 'Все'))  # добавляем выбор всех пользователей
    applicant_ids_for_export = []

    if request.method == 'POST' and form.validate_on_submit():
        search_criteria = {}
        filters = []

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

        if form.edited_by_user.data:  # Если выбран пользователь
            search_criteria['edited_by_user'] = form.edited_by_user.data

        if form.edited_time_start.data:  # Если указана начальная дата
            search_criteria['edited_time_start'] = form.edited_time_start.data

        if form.edited_time_end.data:  # Если указана конечная дата
            search_criteria['edited_time_end'] = form.edited_time_end.data

        for field_name in ['birth_date', 'last_visit']:
            start_date = form[f'{field_name}_start'].data
            end_date = form[f'{field_name}_end'].data

            if start_date and end_date:
                search_criteria[f'{field_name}_start'] = start_date
                search_criteria[f'{field_name}_end'] = end_date
            elif start_date or end_date:  # Если заполнена только одна дата
                flash(f'Заполните обе даты для "{field_name.replace("_", " ").title()}"', 'error')
                return render_template('search_applicants.html', form=form, applicants=applicants)

        # Построение запроса с учетом last_visit
        last_visit_sq = (
            db.session.query(
                Vizit.applicant_id,
                func.max(Vizit.visit_date).label('last_visit_date')
            )
            .group_by(Vizit.applicant_id)
            .subquery()
        )

        query = db.session.query(Applicant).outerjoin(
            last_visit_sq, Applicant.id == last_visit_sq.c.applicant_id
        )

        for field_name, value in search_criteria.items():

            if field_name == 'last_name':
                filters.append(func.upper(getattr(Applicant, field_name)).contains(value))
            elif field_name == 'last_name_exact':
                filters.append(func.upper(getattr(Applicant, field_name)) == value)
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
            elif field_name == 'edited_by_user':
                filters.append(Applicant.edited_by_user_id == value)
            elif field_name == 'edited_time_start':
                filters.append(Applicant.edited_time >= value)
            elif field_name == 'edited_time_end':
                filters.append(Applicant.edited_time <= value)
            else:
                filters.append(getattr(Applicant, field_name) == value)

        if filters:
            query = query.filter(and_(*filters))
            # print(query)

        applicants = query.all()

        if applicants:  # Убедимся, что список не пуст
            applicant_ids_for_export = [app.id for app in applicants]
        else:
            applicant_ids_for_export = []

    return render_template(
        'search_applicants.html',
        form=form,
        applicants=applicants,
        applicant_ids_for_export=applicant_ids_for_export
    )


@applicants_bp.route('/export/found_data', methods=['POST'])
@login_required
@role_required('admin', 'dload')
@thread
def export_found_data():
    applicant_ids_str = request.form.get('applicant_ids')
    if not applicant_ids_str:
        flash('Не выбраны заявители для экспорта.', 'warning')
        return redirect(url_for('your_blueprint.search_applicants'))  # Вернитесь на страницу поиска

    try:
        applicant_ids = [int(id_str) for id_str in applicant_ids_str.split(',') if id_str.strip()]
    except ValueError:
        flash('Некорректный формат ID заявителей.', 'error')
        return redirect(url_for('your_blueprint.search_applicants'))

    if not applicant_ids:
        flash('Список ID заявителей для экспорта пуст.', 'warning')
        return redirect(url_for('your_blueprint.search_applicants'))

    # --- Сбор данных для листа "Заявители" ---
    applicants_query = db.session.query(Applicant).options(
        # Загружаем связанные данные, чтобы избежать N+1 запросов и иметь доступ к именам
        # joinedload(Applicant.gender),
        # joinedload(Applicant.citizenship),
        # joinedload(Applicant.registration_region),
        # joinedload(Applicant.residence_region),
        joinedload(Applicant.edited_by_user).joinedload(User.department),  # Если нужно ФИО и отдел редактора
        # Добавьте joinedload для всех FK, которые вы хотите заменить на имена
        # например, joinedload(Applicant.some_other_relation)
    ).filter(Applicant.id.in_(applicant_ids)).order_by(Applicant.last_name, Applicant.first_name)

    found_applicants = applicants_query.all()

    applicants_data_for_excel = []
    for app in found_applicants:
        data_row = {
            'ID': app.id,
            'Фамилия': app.last_name,
            'Имя': app.first_name,
            'Отчество': app.middle_name,
            'Дата рождения': app.birth_date.strftime('%d.%m.%Y') if app.birth_date else None,
            # 'Пол': app.gender.name if app.gender else None,  # Предполагаем, что у Gender есть поле 'name'
            # 'Гражданство': app.citizenship.name if app.citizenship else None,  # Предполагаем 'name'
            'СНИЛС': app.snils_number,
            'Мед. книжка №': app.medbook_number,
            # 'Регион регистрации': app.registration_region.name if app.registration_region else None,
            # Предполагаем 'name'
            'Адрес регистрации': app.registration_address,
            # 'Регион проживания': app.residence_region.name if app.residence_region else None,  # Предполагаем 'name'
            'Адрес проживания': app.residence_address,
            'Телефон': app.phone_number,
            'Email': app.email,
            # 'Дата создания записи': app.created_time.strftime('%d.%m.%Y %H:%M:%S') if app.created_time else None,
            'Дата последнего редактирования': app.edited_time.strftime(
                '%d.%m.%Y %H:%M:%S') if app.edited_time else None,
            'Кем редактировано (логин)': app.edited_by_user.username if app.edited_by_user else None,
            'Доп. информация': app.additional_info
            # Исключаем: is_editing_now, editing_by_id, editing_started_at
        }
        applicants_data_for_excel.append(data_row)
    df_applicants = pd.DataFrame(applicants_data_for_excel)

    # --- Сбор данных для листа "Визиты" ---
    vizits_query = db.session.query(Vizit).options(
        joinedload(Vizit.applicant),  # для medbook_number, snils_number
        joinedload(Vizit.contingent),
        joinedload(Vizit.attestation_type),
        joinedload(Vizit.work_field),
        joinedload(Vizit.applicant_type),
        joinedload(Vizit.contract).joinedload(Contract.organization)  # Чтобы сразу получить организацию контракта
    ).filter(Vizit.applicant_id.in_(applicant_ids)).order_by(Vizit.applicant_id, Vizit.visit_date)

    found_vizits = vizits_query.all()

    vizits_data_for_excel = []
    contract_ids_from_vizits = set()  # Для сбора уникальных ID контрактов

    for vizit in found_vizits:
        if vizit.contract_id:
            contract_ids_from_vizits.add(vizit.contract_id)
        data_row = {
            'Мед. книжка заявителя': vizit.applicant.medbook_number if vizit.applicant else None,
            'СНИЛС заявителя': vizit.applicant.snils_number if vizit.applicant else None,
            'ID визита': vizit.id,
            'ID заявителя (FK)': vizit.applicant_id,  # Можно добавить ФИО для удобства
            'ФИО заявителя': f"{vizit.applicant.last_name} {vizit.applicant.first_name} {vizit.applicant.middle_name or ''}".strip() if vizit.applicant else None,
            'Дата визита': vizit.visit_date.strftime('%d.%m.%Y %H:%M:%S') if vizit.visit_date else None,
            'Контингент': vizit.contingent.name if vizit.contingent else None,  # Предполагаем 'name'
            'Тип аттестации': vizit.attestation_type.name if vizit.attestation_type else None,  # Предполагаем 'name'
            'Область работ': vizit.work_field.name if vizit.work_field else None,  # Предполагаем 'name'
            'Тип заявителя (в визите)': vizit.applicant_type.name if vizit.applicant_type else None,
            # Предполагаем 'name'
            'ID контракта (FK)': vizit.contract_id,
            'Номер контракта': vizit.contract.number if vizit.contract else None,
            'Доп. информация по визиту': vizit.additional_info
        }
        vizits_data_for_excel.append(data_row)
    df_vizits = pd.DataFrame(vizits_data_for_excel)

    # --- Сбор данных для листа "Контракты" ---
    contracts_data_for_excel = []
    if contract_ids_from_vizits:
        contracts_query = db.session.query(Contract).options(
            joinedload(Contract.organization)  # Для ИНН организации
        ).filter(Contract.id.in_(list(contract_ids_from_vizits))).order_by(Contract.contract_date)

        found_contracts = contracts_query.all()

        for contract in found_contracts:
            data_row = {
                'ID контракта': contract.id,
                'Номер контракта': contract.number,
                'Наименование контракта': contract.name,
                'Дата заключения': contract.contract_date.strftime('%d.%m.%Y') if contract.contract_date else None,
                'Срок действия до': contract.expiration_date.strftime('%d.%m.%Y') if contract.expiration_date else None,
                'Пролонгирован': 'Да' if contract.is_extended else 'Нет',
                'ID организации (FK)': contract.organization_id,
                'ИНН организации': contract.organization.inn if contract.organization and hasattr(contract.organization,
                                                                                                  'inn') else None,
                # Предполагаем у Organization есть 'inn'
                'Наименование организации': contract.organization.name if contract.organization and hasattr(
                    contract.organization, 'name') else None,
                'Доп. информация по контракту': contract.additional_info
            }
            contracts_data_for_excel.append(data_row)
    df_contracts = pd.DataFrame(contracts_data_for_excel)

    # --- Генерация Excel файла ---
    output = BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df_applicants.to_excel(writer, sheet_name='Заявители', index=False)
        df_vizits.to_excel(writer, sheet_name='Визиты', index=False)
        if not df_contracts.empty:
            df_contracts.to_excel(writer, sheet_name='Контракты', index=False)
        # Если df_contracts пуст, лист "Контракты" просто не будет создан, что нормально.

    output.seek(0)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"export_applicants_{timestamp}.xlsx"

    return send_file(
        output,
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        as_attachment=True,  # Для Flask 2.0+ используйте download_name
        download_name=filename  # Для Flask 2.0+
        # attachment_filename=filename # Для старых версий Flask
    )

# @event.listens_for(Applicant, 'before_update')
# def receive_before_update(mapper, connection, target):
#     target.edited_time = datetime.utcnow()
#     target.edited_by_user = current_user.id # Записываем id текущего пользователя
