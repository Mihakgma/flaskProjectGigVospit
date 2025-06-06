from datetime import datetime

from flask import (Blueprint,
                   render_template,
                   request,
                   redirect,
                   url_for,
                   flash, jsonify, current_app)
from flask_login import login_required, current_user
from sqlalchemy.orm import load_only, joinedload
from wtforms.validators import ValidationError

from functions.access_control import role_required
from models.models import Contract, Organization, Vizit, Applicant, get_current_nsk_time
from database import db

from forms.forms import ContractForm, ApplicantSearchForm
from utils.crud_classes import UserCrudControl
from utils.pages_lock.lock_info import LockInfo
from utils.pages_lock.lock_management import PageLocker

contracts_bp = Blueprint('contracts', __name__)


@contracts_bp.route('/add', methods=['GET', 'POST'])
@login_required
@role_required('super', 'admin', 'moder', 'oper', )
def add_contract():
    form = ContractForm()

    if request.method == 'POST':
        if form.validate_on_submit():
            try:
                form.check_duplicates()
                new_contract = Contract(
                    number=form.number.data,
                    contract_date=form.contract_date.data,
                    name=form.name.data,
                    expiration_date=form.expiration_date.data,
                    is_extended=form.is_extended.data,
                    organization_id=form.organization_id.data,  # Присваиваем выбранную организацию
                    info=form.info.data
                )
                db.session.add(new_contract)
                user_crud_control = UserCrudControl(user=current_user,
                                                    db_object=db)
                user_crud_control.commit_other_table()
                db.session.commit()
                flash('Новый контракт успешно добавлен!', 'success')
                return redirect(url_for('contracts.contract_details',
                                        contract_id=new_contract.id))
            except ValidationError as e:
                db.session.rollback()
                # flash(e)
                flash('Договор уже добавлен в БД.'
                      'Пожалуйста, попробуйте внести другой номер, дату подписания или организацию.')
            except Exception as e:
                db.session.rollback()
                print(f"Ошибка при добавлении контракта: {e}")
                flash('Произошла ошибка при добавлении контракта. Попробуйте позже.', 'danger')

    return render_template('add_contract.html', form=form)


@contracts_bp.route('/details/<int:contract_id>')
@login_required
@role_required('anyone')
def contract_details(contract_id):
    contract = Contract.query.options(
        joinedload(Contract.organization)  # Если есть связь с организацией
    ).get_or_404(contract_id)

    related_vizits_list = Vizit.query.filter_by(contract_id=contract.id).all()

    # 2. Количество визитов, к которым прикреплен текущий контракт
    num_related_vizits = len(related_vizits_list)

    # 3. Количество уникальных заявителей, к визитам которых прикреплен текущий контракт
    unique_applicant_ids = set()
    if related_vizits_list:  # Проверяем, что список не пуст
        for vizit in related_vizits_list:
            if vizit.applicant_id:  # Убедимся, что у визита есть заявитель
                unique_applicant_ids.add(vizit.applicant_id)

    num_unique_applicants = len(unique_applicant_ids)

    return render_template('contract_details.html',  # Имя вашего шаблона деталей контракта
                           contract=contract,
                           num_related_vizits=num_related_vizits,
                           num_unique_applicants=num_unique_applicants)


@contracts_bp.route('/search', methods=['GET'])
@login_required
@role_required('anyone')
def search_contracts():
    q = request.args.get('q')  # Название организации
    page = int(request.args.get('page', 1))
    start_date = request.args.get('start_date')  # Дата подписания (от)
    end_date = request.args.get('end_date')  # Дата подписания (до)
    expiration_start_date = request.args.get('expiration_start_date')
    expiration_end_date = request.args.get('expiration_end_date')
    contract_name = request.args.get('contract_name')

    try:
        if start_date:
            start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
        if end_date:
            end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
        if expiration_start_date:
            expiration_start_date = datetime.strptime(expiration_start_date, '%Y-%m-%d').date()
        if expiration_end_date:
            expiration_end_date = datetime.strptime(expiration_end_date, '%Y-%m-%d').date()
    except ValueError:
        return jsonify({'error': 'Неверный формат даты'}), 400

    query = Contract.query.options(load_only(
        Contract.id,
        Contract.number,
        Contract.name,
        Contract.contract_date,
        Contract.expiration_date,
        Contract.is_extended,
        Contract.organization_id,
        Contract.info
    ))

    if q:  # Поиск по названию организации
        query = query.join(Organization).filter(Organization.name.ilike(f"%{q}%"))

    if start_date:
        query = query.filter(Contract.contract_date >= start_date)

    if end_date:
        query = query.filter(Contract.contract_date <= end_date)

    if expiration_start_date:
        query = query.filter(Contract.expiration_date >= expiration_start_date)

    if expiration_end_date:
        query = query.filter(Contract.expiration_date <= expiration_end_date)

    if contract_name:
        query = query.filter(Contract.name.ilike(f"%{contract_name}%"))

    contracts = query.paginate(page=page, per_page=30, error_out=False)

    results = []
    for contract in contracts.items:
        org_name = None
        if contract.organization_id:
            org = Organization.query.get(contract.organization_id)
            if org:
                org_name = org.name

        results.append({
            'id': contract.id,
            'number': contract.number,
            'name': contract.name,
            'organization_name': org_name,
            'contract_date': contract.contract_date.isoformat() if contract.contract_date else None,
            'expiration_date': contract.expiration_date.isoformat() if contract.expiration_date else None,
            'detail_url': f'/contracts/{contract.id}'
        })

    return render_template('search_contracts.html',
                           contracts=results,
                           total_count=contracts.total)


@contracts_bp.route('/<int:contract_id>/edit', methods=['GET', 'POST'])
@login_required
@role_required('super', 'admin', 'moder')
def edit_contract(contract_id):
    timeout = PageLocker.get_timeout()
    print(f'Timeout: {timeout} secs...')
    lock_info = LockInfo("contracts_bp",
                         "edit_contract",
                         contract_id,
                         current_user.id)
    if PageLocker.lock_page(lock_data=lock_info):
        flash(f'У Вас есть <{timeout}> секунд на редактирование '
              f'и сохранение изменений для текущей страницы...',
              'warning')
        contract = Contract.query.get_or_404(contract_id)

        contract_form = ContractForm()

        if request.method == 'POST':
            # Важно: В POST запросе WTForms по умолчанию пытается заполнить формы из request.form.
            # Если валидация не пройдёт, формы сохранят введённые, но невалидные данные.

            # --- Обработка отправки формы редактирования контракта ---
            # Проверяем, была ли нажата кнопка 'submit' из ContractForm
            if 'submit' in request.form:
                current_app.logger.debug("Обнаружена отправка формы редактирования контракта.")
                if contract_form.validate_on_submit():
                    try:
                        contract_form.populate_obj(contract)
                        user_crud_control = UserCrudControl(user=current_user,
                                                            db_object=db)
                        user_crud_control.commit_other_table()
                        db.session.commit()
                        flash('Договор успешно обновлен!', 'success')
                        PageLocker.unlock_page(lock_data=lock_info)
                        return redirect(url_for('contracts.contract_details', contract_id=contract.id))
                    except Exception as e:
                        db.session.rollback()
                        flash(f'Ошибка при обновлении договора: {e}', 'error')
                        current_app.logger.error(f"Ошибка обновления договора: {e}")
                else:
                    # Если форма контракта не прошла валидацию, её ошибки уже будут в contract_form.errors
                    # и она сохранит введенные пользователем значения. Flash-сообщения покажут ошибки.
                    for field, errors in contract_form.errors.items():
                        for error in errors:
                            flash(f"Ошибка в поле '{contract_form[field].label.text}': {error}", 'error')
                    current_app.logger.debug(f"Ошибки валидации ContractForm: {contract_form.errors}")

            else:
                # Этот блок выполняется, если POST-запрос был отправлен, но ни одна из
                # ожидаемых кнопок submit (из ContractForm или ApplicantSearchForm) не была нажата.
                # Это может быть POST от формы открепления визита, или другой формы.
                current_app.logger.warning(
                    f"Неопознанный POST-запрос на странице edit_contract. request.form: {request.form}")
                # В этом случае, contract_form должна быть заполнена данными из БД,
                # чтобы избежать "сброса" полей контракта.
                contract_form = ContractForm(obj=contract)

        # --- Инициализация или предзаполнение contract_form для GET-запроса или после POST,
        # если не её кнопка была нажата (чтобы не сбросить данные контракта) ---
        if request.method == 'GET' or ('submit' not in request.form and not contract_form.errors):
            # Если это GET или POST, который не был связан с ContractForm,
            # и у contract_form нет ошибок, то предзаполняем ее из объекта contract.
            # Если у contract_form уже есть ошибки (например, после неудачного submit),
            # то мы не будем ее перезаписывать, чтобы показать ошибки пользователю.
            if request.method == 'GET' or not contract_form.data.get(
                    'number'):  # Пример дополнительной проверки, что форма не была отправлена
                contract_form = ContractForm(obj=contract)
            # Если contract_form.data.get('number') пуст, это может означать, что форма была отправлена
            # без данных, и мы хотим отобразить ошибки.

        current_linked_visits = Vizit.query.filter_by(contract_id=contract.id).options(joinedload(Vizit.applicant)).all()

        return render_template('edit_contract.html',
                               contract=contract,
                               contract_form=contract_form,
                               # applicant_search_form=applicant_search_form,
                               # applicants_found=applicants_found,
                               current_linked_visits=current_linked_visits,
                               # show_applicant_search_collapse=show_applicant_search_collapse,
                               timeout=timeout)
    else:
        return redirect(url_for('contracts.contract_details',
                                contract_id=contract_id))
    PageLocker.unlock_page(lock_data=lock_info)


# ОПЦИОНАЛЬНО: Роут для открепления визита от контракта
@contracts_bp.route('/unlink_visit/<int:visit_id>', methods=['POST'])
@login_required
@role_required('super', 'admin', 'moder')  # Кто может откреплять визиты
def unlink_visit(visit_id):
    visit = Vizit.query.get_or_404(visit_id)
    contract_id = visit.contract_id  # Сохраняем ID контракта для редиректа
    visit.updated_at = get_current_nsk_time()
    visit.updated_by_user_id = current_user.id

    if contract_id:
        visit.contract_id = None  # Открепляем визит
        try:
            user_crud_control = UserCrudControl(user=current_user,
                                                db_object=db)
            user_crud_control.commit_other_table()
            db.session.commit()
            flash('Визит успешно откреплен от договора.', 'info')
        except Exception as e:
            db.session.rollback()
            flash(f'Ошибка при откреплении визита: {e}', 'error')
            print(f"Ошибка при откреплении визита: {e}")
    else:
        flash('Визит не был прикреплен к договору.', 'info')

    # Перенаправляем обратно на страницу редактирования контракта
    return redirect(url_for('contracts.edit_contract', contract_id=contract_id))
