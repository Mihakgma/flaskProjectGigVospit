from flask import (Blueprint,
                   render_template)
from flask_login import login_required

from functions.access_control import role_required

routes_bp = Blueprint('routes', __name__)

ROUTES_INFO = [
    {'title': 'Добавить пользователя', 'route': 'users.add_user'},
    {'title': 'Отобразить пользователей', 'route': 'users.user_list'},
    {'title': 'Добавить заявителя', 'route': 'applicants.add_applicant'},
    {'title': 'Искать заявителя', 'route': 'applicants.search_applicants'},
    {'title': 'Добавить организацию', 'route': 'organizations.add_organization'},
    {'title': 'Управление организациями', 'route': 'organizations.manage_orgs'},
    {'title': 'Добавить контракт', 'route': 'contracts.add_contract'},
    {'title': 'Искать контракты', 'route': 'contracts.search_contracts'},
    {'title': 'Вход', 'route': 'auth.login'},
    # {'title': 'Выход', 'route': 'auth.logout'}
]


@routes_bp.route('/')
@login_required
@role_required('anyone')
def index():
    return render_template('index.html', routes=ROUTES_INFO)
