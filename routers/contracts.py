from datetime import datetime

from flask import (Blueprint,
                   render_template,
                   request,
                   redirect,
                   url_for,
                   flash, jsonify)
from flask_login import login_required
from sqlalchemy.orm import load_only, joinedload
from wtforms.validators import ValidationError

from functions.access_control import role_required
from models.models import Contract, Organization, Vizit, Applicant
from database import db

from forms.forms import ContractForm, ApplicantSearchForm

contracts_bp = Blueprint('contracts', __name__)


@contracts_bp.route('/add', methods=['GET', 'POST'])
@login_required
@role_required('admin', 'moder', 'oper', )
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
                db.session.commit()
                flash('Новый контракт успешно добавлен!', 'success')
                return redirect(url_for('contract_details', contract_id=new_contract.id))
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
@role_required('admin', 'moder', 'oper')
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
@role_required('admin', 'moder')  # Ограничьте доступ по ролям, кто может редактировать контракты
def edit_contract(contract_id):
    contract = Contract.query.get_or_404(contract_id)  # Получаем контракт или 404

    contract_form = ContractForm()  # Основная форма для данных контракта
    applicant_search_form = ApplicantSearchForm()  # Форма для поиска заявителей

    applicants_found = []  # Список для хранения найденных заявителей

    # Определяем, какая форма была отправлена (если это POST-запрос)
    if request.method == 'POST':
        # Проверяем, была ли отправлена форма редактирования контракта
        if contract_form.submit.data and contract_form.validate():
            print("Отправлена форма редактирования контракта.")
            try:
                # Обновляем поля объекта contract данными из формы
                contract_form.populate_obj(contract)

                # Если организация изменилась, обновим связь
                if contract.organization_id != contract_form.organization_id.data:
                    contract.organization = Organization.query.get(contract_form.organization_id.data)

                db.session.commit()
                flash('Договор успешно обновлен!', 'success')
                return redirect(url_for('contracts.contract_details', contract_id=contract.id))
            except Exception as e:
                db.session.rollback()
                flash(f'Ошибка при обновлении договора: {e}', 'error')
                print(f"Ошибка обновления договора: {e}")
        # Проверяем, была ли отправлена форма поиска заявителей
        elif applicant_search_form.search_submit.data and applicant_search_form.validate():
            print("Отправлена форма поиска заявителей.")

            # Логика поиска заявителей
            applicants_query = Applicant.query

            if applicant_search_form.last_name.data:
                if applicant_search_form.last_name_exact.data:
                    applicants_query = applicants_query.filter(
                        Applicant.last_name == applicant_search_form.last_name.data)
                else:
                    applicants_query = applicants_query.filter(
                        Applicant.last_name.ilike(f'%{applicant_search_form.last_name.data}%'))

            # Используем собранные full_snils_number и full_medbook_number
            if applicant_search_form.full_snils_number:
                applicants_query = applicants_query.filter(
                    Applicant.snils_number == applicant_search_form.full_snils_number)
            if applicant_search_form.full_medbook_number:
                applicants_query = applicants_query.filter(
                    Applicant.medbook_number == applicant_search_form.full_medbook_number)

            if applicant_search_form.birth_date_start.data:
                applicants_query = applicants_query.filter(
                    Applicant.birth_date >= applicant_search_form.birth_date_start.data)
            if applicant_search_form.birth_date_end.data:
                applicants_query = applicants_query.filter(
                    Applicant.birth_date <= applicant_search_form.birth_date_end.data)

            if applicant_search_form.last_visit_start.data:
                # Поиск визитов по дате и затем фильтрация заявителей
                visited_applicant_ids = [v.applicant_id for v in Vizit.query.filter(
                    Vizit.visit_date >= applicant_search_form.last_visit_start.data).distinct(Vizit.applicant_id).all()]
                applicants_query = applicants_query.filter(Applicant.id.in_(visited_applicant_ids))
            if applicant_search_form.last_visit_end.data:
                visited_applicant_ids = [v.applicant_id for v in Vizit.query.filter(
                    Vizit.visit_date <= applicant_search_form.last_visit_end.data).distinct(Vizit.applicant_id).all()]
                applicants_query = applicants_query.filter(Applicant.id.in_(visited_applicant_ids))

            if applicant_search_form.registration_address.data:
                applicants_query = applicants_query.filter(
                    Applicant.registration_address.ilike(f"%{applicant_search_form.registration_address.data}%"))
            if applicant_search_form.residence_address.data:
                applicants_query = applicants_query.filter(
                    Applicant.residence_address.ilike(f"%{applicant_search_form.residence_address.data}%"))

            # updated_by_user - если это ID пользователя, то нужен User.query.filter_by(id=...)
            # Если это имя пользователя, то Applicant.updated_by.ilike(...)
            # Для простоты пока оставим как есть, если это просто строка
            if applicant_search_form.updated_by_user.data:
                # Предположим, что это строка, которую нужно найти в поле (если такое поле есть в Applicant)
                # Или если это поле связано с User-моделью, то нужно фильтровать по ней
                pass  # Тут нужно добавить логику фильтрации по обновляющему пользователю

            if applicant_search_form.updated_at_start.data:
                applicants_query = applicants_query.filter(
                    Applicant.updated_at >= applicant_search_form.updated_at_start.data)
            if applicant_search_form.updated_at_end.data:
                applicants_query = applicants_query.filter(
                    Applicant.updated_at <= applicant_search_form.updated_at_end.data)

            applicants_found = applicants_query.limit(50).all()  # Ограничиваем количество результатов
            if not applicants_found:
                flash('Заявители по заданным критериям не найдены.', 'info')

        # Если кнопка "Очистить" была нажата (через JS-функцию resetApplicantSearchForm, которая перезагружает форму)
        elif 'clear_search_button' in request.form:  # Это проверка, если вы добавили скрытое поле с таким именем
            applicant_search_form = ApplicantSearchForm()  # Пересоздаем форму, чтобы очистить данные
            flash('Поля поиска очищены.', 'info')
        else:
            # Если POST-запрос, но ни одна форма не была валидной или распознана
            print("POST-запрос получен, но форма не валидна или не распознана.")
            print("Ошибки ContractForm:", contract_form.errors)
            print("Ошибки ApplicantSearchForm:", applicant_search_form.errors)
            for field, errors in contract_form.errors.items():
                for error in errors:
                    flash(f"Ошибка в поле '{contract_form[field].label.text}': {error}", 'error')
            for field, errors in applicant_search_form.errors.items():
                for error in errors:
                    flash(f"Ошибка в поле '{applicant_search_form[field].label.text}': {error}", 'error')

    # Для GET-запроса или если POST-запрос был для поиска, но не для обновления контракта
    if request.method == 'GET' or (request.method == 'POST' and not contract_form.submit.data):
        # Предзаполняем форму контракта данными из объекта contract
        contract_form = ContractForm(obj=contract)

        # Получаем визиты, уже прикрепленные к текущему контракту, для отображения
    current_linked_visits = Vizit.query.filter_by(contract_id=contract.id).options(joinedload(Vizit.applicant)).all()

    return render_template('edit_contract.html',
                           contract=contract,
                           contract_form=contract_form,
                           applicant_search_form=applicant_search_form,
                           applicants_found=applicants_found,
                           current_linked_visits=current_linked_visits)


# НОВЫЙ РОУТ: Прикрепление нового визита к контракту для выбранного заявителя
@contracts_bp.route('/<int:contract_id>/link_visit/<int:applicant_id>', methods=['POST'])
@login_required
@role_required('admin', 'moder', 'oper')  # Кто может прикреплять визиты
def link_visit_to_contract(contract_id, applicant_id):
    contract = Contract.query.get_or_404(contract_id)
    applicant = Applicant.query.get_or_404(applicant_id)

    # Здесь вы можете создать новый визит, привязав его к контракту и заявителю
    # Для простоты, создадим минимальный визит с текущей датой.
    # В реальном приложении вы, возможно, захотите форму для ввода даты визита, типа и т.д.
    new_visit = Vizit(
        applicant_id=applicant.id,
        contract_id=contract.id,
        visit_date=datetime.utcnow().date(),  # Дата визита
        status='Планируется',  # Пример статуса
        # Добавьте другие поля для модели Vizit, если они обязательны
    )
    db.session.add(new_visit)
    try:
        db.session.commit()
        flash(f'Новый визит для заявителя "{applicant.full_name}" успешно создан и прикреплен к договору!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Ошибка при создании визита: {e}', 'error')
        print(f"Ошибка при создании визита: {e}")

    # Перенаправляем обратно на страницу редактирования контракта
    return redirect(url_for('contracts.edit_contract', contract_id=contract.id))


# ОПЦИОНАЛЬНО: Роут для открепления визита от контракта
@contracts_bp.route('/unlink_visit/<int:visit_id>', methods=['POST'])
@login_required
@role_required('admin', 'moder')  # Кто может откреплять визиты
def unlink_visit(visit_id):
    visit = Vizit.query.get_or_404(visit_id)
    contract_id = visit.contract_id  # Сохраняем ID контракта для редиректа

    if contract_id:
        visit.contract_id = None  # Открепляем визит
        try:
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
