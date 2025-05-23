from datetime import datetime

from flask import (Blueprint,
                   render_template,
                   redirect,
                   url_for,
                   flash,
                   jsonify,
                   request)
from flask_login import login_required
from sqlalchemy import text, and_
from sqlalchemy.orm import load_only
from sqlalchemy.orm.exc import FlushError
from sqlalchemy.sql.functions import func

from functions.access_control import role_required
from models.models import Organization, Contract
from database import db

from sqlalchemy.exc import IntegrityError, SQLAlchemyError

from forms.forms import OrganizationAddForm

orgs_bp = Blueprint('organizations', __name__)


@orgs_bp.route('/add', methods=['GET', 'POST'])
@login_required
@role_required('admin', 'moder', 'oper', )
def add_organization():
    form = OrganizationAddForm()

    if form.validate_on_submit():
        try:
            org = Organization(
                name=form.name.data,
                inn=form.inn.data,
                address=form.address.data,
                phone_number=form.phone_number.data,
                email=form.email.data,
                is_active=form.is_active.data,
                info=form.info.data
            )
            db.session.add(org)
            db.session.commit()
            flash('Организация успешно добавлена!', 'success')
            return redirect(url_for('routes.organization_details',
                                    organization_id=org.id))

        except IntegrityError as e:
            db.session.rollback()
            if 'UNIQUE constraint failed' in str(e):
                if 'inn' in str(e):
                    flash('Организация с таким ИНН уже существует.', 'danger')
                else:  # Для других потенциальных уникальных полей
                    flash('Произошла ошибка, связанная с уникальностью данных. Проверьте введённую информацию.',
                          'danger')
            else:
                print(f"Ошибка при добавлении организации: {e}")
                flash('Произошла ошибка при добавлении организации. Попробуйте позже.', 'danger')

        except Exception as e:
            db.session.rollback()
            print(f"Ошибка при добавлении организации: {e}")
            flash('Произошла ошибка при добавлении организации. Попробуйте позже.', 'danger')
    return render_template('add_organization.html',
                           form=form,
                           title="Добавить организацию")


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


# --- Маршрут для страницы поиска и отображения результатов ---
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
        filters.append(Organization.inn.ilike(f"%{search_inn}%"))
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
    edit_form = OrganizationAddForm()

    return render_template(
        'manage_orgs.html',
        organizations=organizations_pagination,  # Объект пагинации
        search_name=search_name,  # Возвращаем введенные значения в форму поиска
        search_inn=search_inn,
        search_email=search_email,
        edit_form=edit_form  # Передаем форму редактирования в шаблон
    )


# --- AJAX Маршрут для сохранения изменений организации ---
@orgs_bp.route('/api/organizations/<int:org_id>', methods=['POST'])
@login_required
@role_required('admin', 'moder', 'oper')
def update_organization_data(org_id):
    organization = Organization.query.get_or_404(org_id)
    # При создании формы для обработки POST-запроса при редактировании,
    # передаем original_org_id, чтобы validate_inn формы знал ID текущего объекта
    form = OrganizationAddForm(request.form, original_org_id=org_id)  # request.form содержит данные из POST

    if form.validate():
        # Если форма валидна (включая проверку уникальности INN с учетом org_id),
        # обновляем поля объекта organization данными из формы
        form.populate_obj(organization)  # Это удобно заполняет поля объекта из формы

        try:
            db.session.commit()
            return jsonify({"success": True, "message": "Данные организации успешно обновлены."})
        # Явно ловим ошибки, которые могут возникнуть на уровне SQLAlchemy после валидации формы
        except (IntegrityError, FlushError, SQLAlchemyError) as e:
            db.session.rollback()
            # Логирование ошибки e для отладки на сервере
            print(f"Database error during organization update (ID: {org_id}): {e}")

            # Попытка определить тип ошибки для более информативного ответа
            error_message = "Произошла ошибка при сохранении данных."
            # Можно добавить более детальную обработку ошибок, если необходимо
            # Например, проверить текст ошибки для конкретных нарушений (например, уникальности)
            # if isinstance(e, IntegrityError) and 'unique constraint' in str(e).lower():
            #    error_message = "Дубликат значения в уникальном поле (например, ИНН)."

            return jsonify({"success": False, "message": error_message}), 500
        except Exception as e:
            # Ловим любые другие неожиданные ошибки
            db.session.rollback()
            print(f"Unexpected error during organization update (ID: {org_id}): {e}")
            return jsonify({"success": False, "message": f"Произошла непредвиденная ошибка: {e}"}), 500

    else:
        # Если форма не прошла валидацию, возвращаем ошибки
        # validate_inn формы уже обработает ошибки формата и уникальности
        return jsonify({"success": False, "errors": form.errors}), 400
