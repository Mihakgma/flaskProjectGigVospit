from flask import (Blueprint,
                   render_template,
                   redirect,
                   url_for,
                   flash)
from flask_login import login_required

from models.models import Organization
from database import db

from sqlalchemy.exc import IntegrityError

from forms.forms import OrganizationAddForm

routes_bp = Blueprint('routes', __name__)  # Создаем blueprint

# Словарь с описанием роутов
ROUTES_INFO = [
    {'title': 'Добавить пользователя', 'route': 'users.add_user'},
    # {'title': 'Детали пользователя', 'route': 'users.user_details'},
    {'title': 'Добавить заявителя', 'route': 'applicants.add_applicant'},
    # {'title': 'Детали заявителя', 'route': 'applicants.applicant_details'},
    {'title': 'Добавить организацию', 'route': 'routes.add_organization'},  # Добавлен route
    # {'title': 'Детали организации', 'route': 'organizations.organization_details'}, # Добавлен route
    {'title': 'Добавить контракт', 'route': 'contracts.add_contract'},  # Добавлен route
    # {'title': 'Детали контракта', 'route': 'contracts.contract_details'}, # Добавлен route
    {'title': 'Регистрация', 'route': 'auth.register'},
    {'title': 'Вход', 'route': 'auth.login'},
    # {'title': 'Выход', 'route': 'auth.logout'}
]


@routes_bp.route('/')
@login_required
def index():
    return render_template('index.html', routes=ROUTES_INFO)


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
