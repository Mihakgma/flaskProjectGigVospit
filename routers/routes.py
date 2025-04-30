from flask import (Blueprint,
                   render_template)
from flask_login import login_required

routes_bp = Blueprint('routes', __name__)  # Создаем blueprint

# Словарь с описанием роутов
ROUTES_INFO = [
    {'title': 'Добавить пользователя', 'route': 'users.add_user'},
    # {'title': 'Детали пользователя', 'route': 'users.user_details'},
    {'title': 'Добавить заявителя', 'route': 'applicants.add_applicant'},
    # {'title': 'Детали заявителя', 'route': 'applicants.applicant_details'},
    {'title': 'Добавить организацию', 'route': 'organizations.add_organization'},  # Добавлен route
    # {'title': 'Детали организации', 'route': 'organizations.organization_details'}, # Добавлен route
    {'title': 'Добавить контракт', 'route': 'contracts.add_contract'},  # Добавлен route
    # {'title': 'Детали контракта', 'route': 'contracts.contract_details'}, # Добавлен route
    {'title': 'Регистрация', 'route': 'auth.register'},
    {'title': 'Вход', 'route': 'auth.login'},
    # {'title': 'Выход', 'route': 'auth.logout'}
]


@routes_bp.route('/')
# @login_required
def index():
    return render_template('index.html', routes=ROUTES_INFO)
