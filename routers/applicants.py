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
                           Vizit, User, Contract, get_current_nsk_time)
from database import db

from datetime import timezone, datetime

from forms.forms import (AddApplicantForm,
                         VizitForm, ApplicantSearchForm, ApplicantEditForm)
from sqlalchemy import and_
from sqlalchemy.sql.expression import func

from utils.crud_classes import UserCrudControl
from utils.pages_lock.lock_info import LockInfo
from utils.pages_lock.lock_management import PageLocker

applicants_bp = Blueprint('applicants', __name__)


@applicants_bp.route('/add', methods=['GET', 'POST'])
@login_required
@role_required('super', 'admin', 'moder', 'oper', )
def add_applicant():
    applicant_form = AddApplicantForm()
    vizit_form = VizitForm()

    if request.method == 'POST':
        if applicant_form.validate_on_submit():  # Валидация формы заявителя
            try:
                new_applicant = Applicant()
                new_applicant.created_by_user_id = current_user.id
                new_applicant.updated_by_user_id = current_user.id
                applicant_form.populate_obj(new_applicant)
                db.session.add(new_applicant)
                user_crud_control = UserCrudControl(user=current_user,
                                                    db_object=db)
                user_crud_control.commit_other_table()
                db.session.flush()

                if vizit_form.validate_on_submit():  # Валидация формы визита
                    new_vizit = Vizit()
                    vizit_form.populate_obj(new_vizit)
                    new_vizit.applicant_id = new_applicant.id
                    new_vizit.visit_date = vizit_form.visit_date.data
                    new_vizit.info = vizit_form.info.data
                    new_vizit.created_by_user_id = current_user.id
                    new_vizit.updated_by_user_id = current_user.id
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

    return render_template('applicants/add_applicant.html',
                           form=applicant_form,
                           vizit_form=vizit_form)


@applicants_bp.route('/details/<int:applicant_id>')
@login_required
@role_required('super', 'admin', 'moder', 'oper', )
def applicant_details(applicant_id):
    applicant = Applicant.query.get_or_404(applicant_id)
    visits = Vizit.query.filter_by(applicant_id=applicant_id).all()
    for visit in visits:
        if not visit.contract:
            flash(f"Визит от {visit.visit_date} не прикреплен к контракту (договору).", category='warning')
    return render_template('applicants/applicant_details.html',
                           applicant=applicant,
                           visits=visits,
                           timezone=timezone)


@applicants_bp.route('/applicant/<int:applicant_id>/edit', methods=['GET', 'POST'])
@login_required
@role_required('super', 'admin', 'moder', 'oper')
def edit_applicant(applicant_id):
    timeout = PageLocker.get_timeout()
    print(f'Timeout: {timeout} secs...')
    lock_info = LockInfo("applicants_bp",
                         "edit_applicant",
                         applicant_id,
                         current_user.id)
    if PageLocker.lock_page(lock_data=lock_info):
        flash(f'У Вас есть <{timeout}> секунд на редактирование '
              f'и сохранение изменений для текущей страницы...',
              'warning')
        applicant = Applicant.query.get_or_404(applicant_id)
        visits = Vizit.query.filter_by(applicant_id=applicant_id).all()
        applicant_form = ApplicantEditForm(obj=applicant)
        applicant_form._obj = applicant
        vizit_form = VizitForm()
        applicant.updated_by_user_id = current_user.id
        applicant.updated_at = get_current_nsk_time()

        if request.method == 'POST':
            # Обработка формы заявителя
            if 'submit' in request.form and applicant_form.validate_on_submit():
                user_crud_control = UserCrudControl(user=current_user,
                                                    db_object=db)
                user_crud_control.commit_other_table()
                applicant_form.populate_obj(applicant)
                db.session.commit()
                flash('Данные заявителя обновлены', 'success')
                PageLocker.unlock_page(lock_data=lock_info)
                return redirect(url_for('applicants.applicant_details',
                                        applicant_id=applicant_id))

            # Обработка формы визита
            elif 'submit_visit' in request.form and vizit_form.validate_on_submit():
                try:
                    new_vizit = Vizit()
                    vizit_form.populate_obj(new_vizit)
                    new_vizit.applicant_id = applicant.id
                    new_vizit.created_by_user_id = current_user.id
                    new_vizit.updated_by_user_id = current_user.id
                    db.session.add(new_vizit)
                    user_crud_control = UserCrudControl(user=current_user,
                                                        db_object=db)
                    user_crud_control.commit_other_table()
                    db.session.commit()
                    flash('Визит добавлен', 'success')
                    PageLocker.unlock_page(lock_data=lock_info)
                    return redirect(url_for('applicants.applicant_details',
                                            applicant_id=applicant_id))
                except Exception as e:
                    db.session.rollback()
                    flash(f"Ошибка при добавлении визита: {str(e)}", 'danger')

            # Обработка ошибок
            if 'submit' in request.form and not applicant_form.validate_on_submit():
                for field, errors in applicant_form.errors.items():
                    for error in errors:
                        flash(f"Ошибка в поле '{getattr(applicant_form, field).label.text}': {error}", 'danger')

            if 'submit_visit' in request.form and not vizit_form.validate_on_submit():
                for field, errors in vizit_form.errors.items():
                    for error in errors:
                        flash(f"Ошибка в поле '{getattr(vizit_form, field).label.text}': {error}", 'danger')

        return render_template('applicants/edit_applicant.html',
                               applicant=applicant,
                               applicant_form=applicant_form,
                               visit_form=vizit_form,
                               visits=visits,
                               timeout=timeout)
    else:
        return redirect(url_for('applicants.applicant_details',
                                applicant_id=applicant_id))


@applicants_bp.route('/search_applicants', methods=['GET', 'POST'])
@login_required
@role_required('anyone')
def search_applicants():
    roles_all_records_access = [
        'admin',
        'moder'
    ]
    up_limit_rows = 100
    form = ApplicantSearchForm(request.form)  # Используем request.form для POST
    applicants = []
    users = User.query.all()
    form.updated_by_user.choices = [(user.id, user.username) for user in users]
    form.updated_by_user.choices.insert(0, (0, 'Все'))  # добавляем выбор всех пользователей
    applicant_ids_for_export = []

    if request.method == 'POST' and form.validate_on_submit():
        search_criteria = {}
        filters = []

        if not any(field.data for field in form if field.name not in ['csrf_token', 'submit', 'last_name_exact']) and \
                not ('snils_part1' in request.form or 'medbook_part1' in request.form):
            flash('Заполните хотя бы одно поле для поиска', 'error')
            return render_template('applicants/search_applicants.html', form=form, applicants=applicants)

        if form.last_name.data:
            if len(form.last_name.data) < 2:
                flash('Фамилия должна содержать не менее 2 символов', 'error')
                return render_template('applicants/search_applicants.html', form=form, applicants=applicants)
            search_criteria['last_name'] = form.last_name.data

        if form.registration_address.data:
            if len(form.registration_address.data) < 2:
                flash('Адрес регистрации должен содержать не менее 2 символов', 'error')
                return render_template('applicants/search_applicants.html', form=form, applicants=applicants)
            search_criteria['registration_address'] = form.registration_address.data

        if form.residence_address.data:
            if len(form.residence_address.data) < 2:
                flash('Адрес проживания должен содержать не менее 2 символов', 'error')
                return render_template('applicants/search_applicants.html', form=form, applicants=applicants)
            search_criteria['residence_address'] = form.residence_address.data

        if 'snils_part1' in request.form:
            snils_parts = [request.form.get(f'snils_part{i}') for i in range(1, 5)]
            snils = ''.join(filter(None, snils_parts))
            if snils:
                try:
                    search_criteria['snils_number'] = int(snils)
                except ValueError:
                    flash('СНИЛС должен содержать только цифры', 'error')
                    return render_template('applicants/search_applicants.html', form=form, applicants=applicants)

        if 'medbook_part1' in request.form:
            medbook_parts = [request.form.get(f'medbook_part{i}') for i in range(1, 5)]
            medbook = ''.join(filter(None, medbook_parts))
            if medbook:
                try:
                    search_criteria['medbook_number'] = int(medbook)
                except ValueError:
                    flash('Номер медкнижки должен содержать только цифры', 'error')
                    return render_template('applicants/search_applicants.html', form=form, applicants=applicants)

        if form.updated_by_user.data:  # Если выбран пользователь
            search_criteria['updated_by_user'] = form.updated_by_user.data

        if form.updated_at_start.data:  # Если указана начальная дата
            search_criteria['updated_at_start'] = form.updated_at_start.data

        if form.updated_at_end.data:  # Если указана конечная дата
            search_criteria['updated_at_end'] = form.updated_at_end.data

        for field_name in ['birth_date', 'last_visit']:
            start_date = form[f'{field_name}_start'].data
            end_date = form[f'{field_name}_end'].data

            if start_date and end_date:
                search_criteria[f'{field_name}_start'] = start_date
                search_criteria[f'{field_name}_end'] = end_date
            elif start_date or end_date:  # Если заполнена только одна дата
                flash(f'Заполните обе даты для "{field_name.replace("_", " ").title()}"', 'error')
                return render_template('applicants/search_applicants.html', form=form, applicants=applicants)

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
                filters.append(getattr(Applicant, field_name).like(f"%{value}%"))
            elif field_name == 'birth_date_start':
                filters.append(Applicant.birth_date >= value)
            elif field_name == 'birth_date_end':
                filters.append(Applicant.birth_date <= value)
            elif field_name == 'last_visit_start':
                filters.append(last_visit_sq.c.last_visit_date >= value)
            elif field_name == 'last_visit_end':
                filters.append(last_visit_sq.c.last_visit_date <= value)
            elif field_name == 'updated_by_user':
                filters.append(Applicant.updated_by_user_id == value)
            elif field_name == 'updated_at_start':
                filters.append(Applicant.updated_at >= value)
            elif field_name == 'updated_at_end':
                filters.append(Applicant.updated_at <= value)
            else:
                filters.append(getattr(Applicant, field_name) == value)

        if filters:
            query = query.filter(and_(*filters))
            # print(query)
        # all records access is restricted by role policy!!!
        roles = current_user.roles
        user_roles = {role.code for role in roles}
        if any(role_name in user_roles for role_name in roles_all_records_access):
            applicants = query.all()
        else:
            applicants = query.all()[:up_limit_rows]
            flash(f"Ролевая политика для вашего доступа ограничивает выдачу записей из БД до <{up_limit_rows}> шт.")
        if applicants:  # Убедимся, что список не пуст
            applicant_ids_for_export = [app.id for app in applicants]
        else:
            applicant_ids_for_export = []

    return render_template(
        'applicants/search_applicants.html',
        form=form,
        applicants=applicants,
        applicant_ids_for_export=applicant_ids_for_export
    )


@applicants_bp.route('/export/found_data', methods=['POST'])
@login_required
@role_required('dload')
@thread
def export_found_data():
    # with app_context.app_context():
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
        joinedload(Applicant.updated_by_user).joinedload(User.department),  # Если нужно ФИО и отдел редактора
        # Добавьте joinedload для всех FK, которые вы хотите заменить на имена
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
            'СНИЛС': app.snils_number,
            'Мед. книжка №': app.medbook_number,
            'Адрес регистрации': app.registration_address,
            'Адрес проживания': app.residence_address,
            'Телефон': app.phone_number,
            'Email': app.email,
            'Дата последнего редактирования': app.updated_at.strftime(
                '%d.%m.%Y %H:%M:%S') if app.updated_at else None,
            'Кем редактировано (логин)': app.updated_by_user.username if app.updated_by_user else None,
            'Доп. информация': app.info
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
            'Тип аттестации': vizit.attestation_type.name if vizit.attestation_type else None,
            # Предполагаем 'name'
            'Область работ': vizit.work_field.name if vizit.work_field else None,  # Предполагаем 'name'
            'Тип заявителя (в визите)': vizit.applicant_type.name if vizit.applicant_type else None,
            'ID контракта (FK)': vizit.contract_id,
            'Номер контракта': vizit.contract.number if vizit.contract else None,
            'Доп. информация по визиту': vizit.info
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
                'Срок действия до': contract.expiration_date.strftime(
                    '%d.%m.%Y') if contract.expiration_date else None,
                'Пролонгирован': 'Да' if contract.is_extended else 'Нет',
                'ID организации (FK)': contract.organization_id,
                'ИНН организации': contract.organization.inn if contract.organization and hasattr(
                    contract.organization,
                    'inn') else None,
                # Предполагаем у Organization есть 'inn'
                'Наименование организации': contract.organization.name if contract.organization and hasattr(
                    contract.organization, 'name') else None,
                'Доп. информация по контракту': contract.info
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
