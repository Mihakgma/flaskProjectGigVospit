from flask import (Blueprint,
                   render_template)
from flask_login import login_required, current_user

from functions.access_control import role_required


routes_bp = Blueprint('routes', __name__)

TOTAL_ACCESS_ROLES = [
    'super',
]
FULL_ACCESS_ROLES = [
    'admin',
    'moder',
    'dload'
]

TOTAL_CONTROL = [
    {'title': 'Добавить пользователя', 'route': 'users.add_user'},
    {'title': 'Отобразить пользователей', 'route': 'users.user_list'},
    {'title': 'Добавить заявителя', 'route': 'applicants.add_applicant'},
    {'title': 'Искать заявителя', 'route': 'applicants.search_applicants'},
    {'title': 'Добавить организацию', 'route': 'organizations.add_organization'},
    {'title': 'Управление организациями', 'route': 'organizations.manage_orgs'},
    {'title': 'Добавить контракт', 'route': 'contracts.add_contract'},
    {'title': 'Искать контракты', 'route': 'contracts.search_contracts'},
    {'title': 'УПРАВЛЕНИЕ ДОСТУПОМ', 'route': 'settings.list_settings'},
    {'title': 'УПРАВЛЕНИЕ БЭКАПОМ', 'route': 'backup_settings.manage_backup_settings'},
    {'title': 'Вход', 'route': 'auth.login'},
    {'title': 'Выход', 'route': 'auth.logout'}
]

FULL_CONTROL = [
    {'title': 'Добавить пользователя', 'route': 'users.add_user'},
    {'title': 'Отобразить пользователей', 'route': 'users.user_list'},
    {'title': 'Добавить заявителя', 'route': 'applicants.add_applicant'},
    {'title': 'Искать заявителя', 'route': 'applicants.search_applicants'},
    {'title': 'Добавить организацию', 'route': 'organizations.add_organization'},
    {'title': 'Управление организациями', 'route': 'organizations.manage_orgs'},
    {'title': 'Добавить контракт', 'route': 'contracts.add_contract'},
    {'title': 'Искать контракты', 'route': 'contracts.search_contracts'},
    {'title': 'УПРАВЛЕНИЕ ДОСТУПОМ', 'route': 'settings.list_settings'},
    {'title': 'Вход', 'route': 'auth.login'},
    {'title': 'Выход', 'route': 'auth.logout'}
]

MEDIUM_CONTROL = [
    {'title': 'Добавить заявителя', 'route': 'applicants.add_applicant'},
    {'title': 'Искать заявителя', 'route': 'applicants.search_applicants'},
    {'title': 'Управление организациями', 'route': 'organizations.manage_orgs'},
    {'title': 'Добавить контракт', 'route': 'contracts.add_contract'},
    {'title': 'Искать контракты', 'route': 'contracts.search_contracts'},
    {'title': 'Вход', 'route': 'auth.login'},
    {'title': 'Выход', 'route': 'auth.logout'}
]


@routes_bp.route('/')
@login_required
@role_required('anyone')
def index():
    user_roles = {role.code for role in current_user.roles}
    if any(role in FULL_ACCESS_ROLES for role in user_roles):
        return render_template('index.html', routes=FULL_CONTROL)
    elif any(role in TOTAL_ACCESS_ROLES for role in user_roles):
        return render_template('index.html', routes=TOTAL_CONTROL)
    else:
        return render_template('index.html', routes=MEDIUM_CONTROL)
