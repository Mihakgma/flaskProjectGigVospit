from flask import (Blueprint,
                   render_template,
                   request,
                   redirect,
                   url_for,
                   flash)
from flask_login import login_required

from models.models import (Contract,
                           Organization)
from database import db

from sqlalchemy.exc import IntegrityError

from forms.forms import (AddContractForm,
                         OrganizationAddForm)

routes_bp = Blueprint('routes', __name__)  # Создаем blueprint

# Словарь с описанием роутов
ROUTES_INFO = [
    {'title': 'Добавить пользователя', 'route': 'users.add_user'},
    # {'title': 'Детали пользователя', 'route': 'users.user_details'},
    {'title': 'Добавить заявителя', 'route': 'applicants.add_applicant'},
    # {'title': 'Детали заявителя', 'route': 'applicants.applicant_details'},
    {'title': 'Добавить организацию', 'route': 'routes.add_organization'}, # Добавлен route
    # {'title': 'Детали организации', 'route': 'organizations.organization_details'}, # Добавлен route
    {'title': 'Добавить контракт', 'route': 'routes.add_contract'}, # Добавлен route
    # {'title': 'Детали контракта', 'route': 'contracts.contract_details'}, # Добавлен route
    {'title': 'Регистрация', 'route': 'auth.register'},
    {'title': 'Вход', 'route': 'auth.login'},
    # {'title': 'Выход', 'route': 'auth.logout'}
]


@routes_bp.route('/')
@login_required
def index():
    # users = User.query.all()  # Или другой запрос, если нужны не все пользователи
    # applicants = Applicant.query.all()
    # organizations = Organization.query.all()
    # contracts = Contract.query.all()
    return render_template('index.html', routes=ROUTES_INFO)


@routes_bp.route('/contracts/add', methods=['GET', 'POST'])
@login_required
def add_contract():
    form = AddContractForm()

    if request.method == 'POST':
        if form.validate_on_submit():
            try:
                new_contract = Contract(
                    number=form.number.data,
                    contract_date=form.contract_date.data,
                    name=form.name.data,
                    expiration_date=form.expiration_date.data,
                    is_extended=form.is_extended.data,
                    organization_id=form.organization_id.data,  # Присваиваем выбранную организацию
                    additional_info=form.additional_info.data
                )

                # Подключаем выбранных заявителей к контракту
                # applicants = Applicant.query.filter(Applicant.id.in_(form.applicants.data)).all()
                # new_contract.applicants.extend(applicants)

                db.session.add(new_contract)
                db.session.commit()
                flash('Новый контракт успешно добавлен!', 'success')
                return redirect(url_for('contract_details', contract_id=new_contract.id))
            except Exception as e:
                db.session.rollback()
                print(f"Ошибка при добавлении контракта: {e}")
                flash('Произошла ошибка при добавлении контракта. Попробуйте позже.', 'danger')

    return render_template('add_contract.html', form=form)


@routes_bp.route('/contracts/<int:contract_id>')
@login_required
def contract_details(contract_id):
    contract = Contract.query.get_or_404(contract_id)
    return render_template('contract_details.html', contract=contract)


@routes_bp.route('/organizations/add', methods=['GET', 'POST'])
@login_required
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
                additional_info=form.additional_info.data
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


@routes_bp.route('/organizations/<int:organization_id>')
@login_required
def organization_details(organization_id):
    organization = Organization.query.get_or_404(organization_id)
    return render_template('organization_details.html',
                           organization=organization,
                           title="Детали организации")
