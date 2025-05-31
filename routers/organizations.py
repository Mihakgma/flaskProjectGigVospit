from datetime import datetime

from flask import (Blueprint,
                   render_template,
                   redirect,
                   url_for,
                   flash,
                   jsonify,
                   request, abort)
from flask_login import login_required, current_user
from sqlalchemy import text, and_
from sqlalchemy.orm import load_only
# from sqlalchemy.orm.exc import FlushError
from sqlalchemy.sql.functions import func

from functions.access_control import role_required
from functions.data_fix import elmk_snils_fix
from models.models import Organization, Contract, get_current_nsk_time
from database import db

from sqlalchemy.exc import IntegrityError

from forms.forms import OrganizationForm
from utils.crud_classes import UserCrudControl
from utils.pages_lock.lock_info import LockInfo
from utils.pages_lock.lock_management import PageLocker

orgs_bp = Blueprint('organizations', __name__)


@orgs_bp.route('/add', methods=['GET', 'POST'])
@login_required
@role_required('admin', 'moder', 'oper', )
def add_organization():
    form = OrganizationForm()  # Создаем форму для GET-запроса или для первоначального отображения

    if request.method == 'POST':
        # **********************************************************************************
        # ВАЖНО: На POST-запросе создаем форму, явно передавая request.form.
        # Это гарантирует, что форма получит данные, даже если __init__ не идеален,
        # хотя после исправления __init__ это становится менее критичным, но не помешает.
        # **********************************************************************************
        form = OrganizationForm(formdata=request.form)

        if form.validate_on_submit():
            try:
                new_org = Organization(
                    inn=form.inn.data,
                    name=form.name.data,
                    address=form.address.data,
                    phone_number=form.phone_number.data,
                    email=form.email.data,
                    is_active=form.is_active.data,
                    info=form.info.data,
                    created_by_user_id=current_user.id,  # Убедитесь, что имена полей в модели совпадают
                    updated_by_user_id=current_user.id,  # Убедитесь, что имена полей в модели совпадают
                    created_at=get_current_nsk_time(),
                    updated_at=get_current_nsk_time(),
                )

                # ***** ВАЖНО: РАСКОММЕНТИРУЙТЕ ЭТУ СТРОКУ! *****
                db.session.add(new_org)
                user_crud_control = UserCrudControl(user=current_user,
                                                    db_object=db)
                user_crud_control.commit_other_table()
                db.session.commit()  # Теперь commit будет пытаться сохранить new_org

                flash('Организация успешно добавлена!', 'success')
                return redirect(url_for('organizations.organization_details',
                                        organization_id=new_org.id))

            except IntegrityError as ie:  # Ловим ошибку уникальности (например, для ИНН)
                db.session.rollback()  # Откатываем изменения
                flash(f'Ошибка: Организация с таким ИНН или другим уникальным полем уже существует. Error: <{ie}>',
                      'danger')
            except Exception as e:  # Ловим любые другие неожиданные ошибки
                db.session.rollback()
                flash(f'Произошла неожиданная ошибка при добавлении организации: {e}', 'danger')
                # В реальном приложении здесь можно логировать ошибку для дальнейшего анализа
        else:
            # Если form.validate_on_submit() вернул False, то форма.errors уже заполнен.
            # Отображаем эти ошибки как flash-сообщения.
            for field_name, errors in form.errors.items():
                field = getattr(form, field_name, None)
                label_text = field.label.text if field and hasattr(field, 'label') else field_name
                for error in errors:
                    flash(f"Ошибка в поле '{label_text}': {error}", 'danger')

    # Рендерим шаблон. Если это GET-запрос, форма будет пустой.
    # Если это POST-запрос с ошибками, форма будет заполнена данными, которые ввел пользователь.
    return render_template('add_organization.html', form=form)


@orgs_bp.route('/details/<int:organization_id>')
@login_required
@role_required('anyone')
def organization_details(organization_id):
    organization = Organization.query.get_or_404(organization_id)
    return render_template('organization_details.html',
                           organization=organization,
                           title="Детали организации")


@orgs_bp.route('/search')
@login_required
@role_required('admin', 'moder', 'oper', )
def search_organizations():
    q = request.args.get('q')
    if not q:
        return
    page = int(request.args.get('page', 1))

    organizations = Organization.query.filter(Organization.name.ilike(f"%{q}%")).paginate(page=page, per_page=30,
                                                                                          error_out=False)
    # work with sqlite3 db
    if organizations.total == 0:
        print("sqlite3 db detected!")
        organizations = Organization.query.filter(
            func.upper(Organization.name).like(f"%{q.upper()}%")  # или lower() для обоих
        ).paginate(page=page, per_page=30, error_out=False)

    return jsonify({
        'items': [{'id': org.id, 'text': org.show_info} for org in organizations.items],
        'total_count': organizations.total
    })


@orgs_bp.route('/check_inn')
def check_inn():
    inn = request.args.get('inn')
    organization = Organization.query.filter_by(inn=inn).first()
    return jsonify({'exists': organization is not None})


@orgs_bp.route('/search')
@login_required
@role_required('admin', 'moder', 'oper')
def search_orgs():
    q = request.args.get('q')
    page = int(request.args.get('page', 1))

    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    contract_name = request.args.get('contract_name')

    # Обработка дат. Важно! Проверка на корректный формат
    try:
        if start_date:
            start_date = datetime.datetime.strptime(start_date, '%Y-%m-%d').date()
        if end_date:
            end_date = datetime.datetime.strptime(end_date, '%Y-%m-%d').date()
    except ValueError:
        return jsonify({'error': 'Неверный формат даты'}), 400

    query = Contract.query.options(load_only('id', 'organization_id', 'name', 'contract_date', 'expiration_date'))

    if q:
        query = query.join(Organization, Contract.organization_id == Organization.id) \
            .filter(text(f"LOWER(Organization.name) LIKE LOWER('%{q}%')"))  # Поиск без upper()

    if start_date:
        query = query.filter(Contract.contract_date >= start_date)

    if end_date:
        query = query.filter(Contract.contract_date <= end_date)

    if contract_name:
        query = query.filter(Contract.name.ilike(f"%{contract_name}%"))

    organizations = query.paginate(page=page, per_page=30, error_out=False)

    results = []
    for contract in organizations.items:
        item = {
            'id': contract.id,
            'name': contract.name,
            'organization_id': contract.organization_id,
            'contract_date': contract.contract_date.isoformat() if contract.contract_date else None,
            'expiration_date': contract.expiration_date.isoformat() if contract.expiration_date else None,
            'detail_url': f'/contracts/{contract.id}'
        }
        results.append(item)

    return jsonify({'items': results, 'total_count': organizations.total})


@orgs_bp.route('/manage', methods=['GET'])
@login_required
@role_required('admin', 'moder', 'oper')
def manage_orgs():
    # Получаем параметры поиска из URL (GET-запрос)
    search_name = request.args.get('search_name', '').strip()
    search_inn = request.args.get('search_inn', '').strip()
    search_email = request.args.get('search_email', '').strip()
    page = request.args.get('page', 1, type=int)
    per_page = 20  # Количество результатов на странице

    query = Organization.query

    # Применяем фильтры по частичному совпадению (используем ilike для без учета регистра)
    filters = []
    if search_name:
        filters.append(Organization.name.ilike(f"%{search_name}%"))
    if search_inn:
        filters.append(Organization.inn.ilike(f"%{elmk_snils_fix(search_inn)}%"))
    if search_email:
        filters.append(Organization.email.ilike(f"%{search_email}%"))

    # Если есть какие-либо фильтры, применяем их
    if filters:
        query = query.filter(and_(*filters))  # Используем and_ для объединения фильтров

    # Сортировка результатов (например, по имени)
    query = query.order_by(Organization.name)

    # Пагинация
    organizations_pagination = query.paginate(page=page, per_page=per_page, error_out=False)

    # Создаем пустую форму редактирования. original_org_id=None по умолчанию,
    # что подходит для формы, не связанной с конкретным объектом.
    # edit_form = OrganizationForm()

    return render_template(
        'manage_orgs.html',
        organizations=organizations_pagination,  # Объект пагинации
        search_name=search_name,  # Возвращаем введенные значения в форму поиска
        search_inn=search_inn,
        search_email=search_email,
        # edit_form=edit_form  # Передаем форму редактирования в шаблон
    )


@orgs_bp.route('/<int:organization_id>/edit', methods=['GET', 'POST'])
@login_required
@role_required('admin', 'moder')
def edit_organization(organization_id):
    lock_info = LockInfo("orgs_bp",
                         "edit_organization",
                         organization_id,
                         current_user.id)
    if PageLocker.lock_page(lock_data=lock_info):
        organization = Organization.query.get(organization_id)
        if not organization:
            abort(404, description="Организация не найдена.")
            print(f"--- Запрос на редактирование организации ID: {organization_id} ---")
        print(f"Метод запроса: {request.method}")
        print(
            f"Организация из БД (до обработки формы): ID={organization.id}, Имя='{organization.name}', ИНН='{organization.inn}'")

        if request.method == 'POST':
            # *******************************************************************
            # &gt;&gt;&gt;&gt;&gt; ИСПРАВЛЕНИЕ: Явно передаем formdata=request.form на POST &lt;&lt;&lt;&lt;&lt;
            # *******************************************************************
            form = OrganizationForm(formdata=request.form, original_org_id=organization.id)
            # Также добавим отладочный вывод сырых данных из request.form
            print(f"Raw request.form content (SERVER): {request.form}")
        else:
            # Для GET-запроса, продолжаем использовать obj=organization для предзаполнения
            form = OrganizationForm(obj=organization, original_org_id=organization.id)

        if form.validate_on_submit():
            print("Форма успешно прошла валидацию!")
            print("Данные из формы (form.data) ПОСЛЕ ВАЛИДАЦИИ:")
            # Выведем каждое поле, чтобы убедиться, что form.data теперь содержит НОВЫЕ значения
            print(f" Name: '{form.name.data}' (Тип: {type(form.name.data)})")
            print(f" INN: '{form.inn.data}' (Тип: {type(form.inn.data)})")
            print(f" Address: '{form.address.data}' (Тип: {type(form.address.data)})")
            print(f" Phone Number: '{form.phone_number.data}' (Тип: {type(form.phone_number.data)})")
            print(f" Email: '{form.email.data}' (Тип: {type(form.email.data)})")
            print(f" Is Active: {form.is_active.data} (Тип: {type(form.is_active.data)})")
            print(f" Info: '{form.info.data}' (Тип: {type(form.info.data)})")

            # Здесь находится ваш код, который выдает "Данные не были изменены!"
            # Это обычно проверка, не модифицирован ли объект.
            # Если вы используете SQLAlchemy's is_modified, то этот код должен быть
            # ПОСЛЕ того, как вы обновите 'organization' из формы.
            # Пример ниже включает такую проверку.

            try:
                # ***************************************************************
                # &gt;&gt;&gt;&gt;&gt; ИСПРАВЛЕНИЕ: Обновляем поля СУЩЕСТВУЮЩЕГО объекта 'organization' &lt;&lt;&lt;&lt;&lt;
                # ***************************************************************
                form.populate_obj(organization)  # &lt;-- Самый чистый и правильный способ!

                print(f"Организация в памяти (ПОСЛЕ populate_obj, ДО commit):")
                print(f" Имя='{organization.name}', ИНН='{organization.inn}'")
                print(f" Is Active='{organization.is_active}'")  # Проверяем и is_active

                # Проверка, были ли внесены изменения в объект в сессии SQLAlchemy
                # (Если вы используете свой собственный check for changes, вставьте его здесь)
                if db.session.is_modified(organization):
                    organization.updated_at = get_current_nsk_time()
                    organization.updated_by_user_id = current_user.id
                    user_crud_control = UserCrudControl(user=current_user,
                                                        db_object=db)
                    user_crud_control.commit_other_table()
                    db.session.commit()  # Сохраняем изменения в базе данных
                    print("db.session.commit() УСПЕШНО ВЫПОЛНЕН.")
                    flash('Данные организации успешно обновлены!', 'success')
                    PageLocker.unlock_page(lock_data=lock_info)
                    return redirect(url_for('organizations.organization_details',
                                            organization_id=organization.id))
                else:
                    db.session.rollback()  # Откатываем, если ничего не изменилось
                    print("Данные не были изменены, commit не требуется.")
                    flash('Данные не были изменены!', 'info')  # &lt;&lt;&lt; Это ваше сообщение!
                PageLocker.unlock_page(lock_data=lock_info)
                return redirect(url_for('organizations.manage_orgs'))
            except Exception as e:
                db.session.rollback()
                print(f"ОШИБКА ПРИ СОХРАНЕНИИ ДАННЫХ: {e}")
                flash(f'Произошла ошибка при сохранении данных: {e}', 'error')

        else:  # Если validate_on_submit() вернул False (для GET-запроса или невалидного POST)
            if request.method == 'POST':
                print("Форма НЕ ПРОШЛА валидацию. Ошибки:")
                print(form.errors)
                for field, errors in form.errors.items():
                    for error in errors:
                        flash(f"Ошибка в поле '{form[field].label.text}': {error}", 'error')

        print("--- Завершение обработки запроса ---")
        return render_template('edit_organization.html', form=form, organization=organization)
    else:
        return redirect(url_for('organizations.manage_orgs'))
    PageLocker.unlock_page(lock_data=lock_info)


@orgs_bp.route('/check_inn_exists', methods=['GET'])
def check_inn_exists():
    inn = request.args.get('inn')
    if not inn:
        return jsonify({'error': 'ИНН не указан'}), 400

    # Проверка на то, что INN состоит только из цифр и имеет правильную длину
    if not inn.isdigit() or not (10 <= len(inn) <= 12):
        return jsonify({'exists': False, 'message': 'ИНН должен содержать от 10 до 12 цифр.'}), 200

    organization = Organization.query.filter_by(inn=inn).first()
    if organization:
        return jsonify({'exists': True, 'message': 'Организация с таким ИНН уже зарегистрирована.'}), 200
    else:
        return jsonify({'exists': False, 'message': 'ИНН свободен.'}), 200

# @orgs_bp.route('/<int:organization_id>/details')
# @login_required  # Добавьте, если нужно, чтобы только авторизованные пользователи могли просматривать
# @role_required('anyone')
# def details_organization(organization_id):
#     organization = Organization.query.get(organization_id)
#     if not organization:
#         abort(404, description="Организация не найдена.")
#
#     return render_template('details_organization.html', organization=organization)
