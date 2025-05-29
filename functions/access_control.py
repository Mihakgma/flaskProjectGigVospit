import functools
from flask import abort, make_response, jsonify, flash, redirect, url_for
from flask_login import current_user, logout_user, AnonymousUserMixin

from models import User
from utils.crud_classes import UserCrudControl


def role_required(*role_names):
    def decorator(original_route):

        @functools.wraps(original_route)
        def decorated_route(*args, **kwargs):

            if not current_user.is_authenticated:
                flash('Вы не авторизованы. Пожалуйста, войдите, чтобы получить доступ.', 'warning')
                return redirect(url_for('auth.login'))
            user = User.query.filter_by(id=current_user.id).first()
            if not user:
                flash('Ваш аккаунт не найден или был удален. Пожалуйста, войдите снова.', 'danger')
                logout_user()  # Удаляем сессию Flask-Login, так как пользователь недействителен.
                return redirect(url_for('auth.login'))
            if not user.is_logged_in:
                flash('Вы не авторизованы. Пожалуйста, войдите, чтобы получить доступ.', 'warning')
                return redirect(url_for('auth.login'))
            if current_user.status.code == "blocked" or current_user.status.code == "block":
                abort(401, description="Пользователь заблокирован")
            UserCrudControl.check_all_users_last_activity(current_user=user)
            if "anyone" in role_names:
                return original_route(*args, **kwargs)
            try:
                roles = current_user.roles
                user_roles = {role.code for role in roles} if roles else set()
                if any(role_name in user_roles for role_name in role_names):
                    return original_route(*args, **kwargs)
                else:
                    response_message = f"ACCESS DENIED - REQUIRED ANY OF THESE ROLES: {', '.join(role_names)}"
                    abort(make_response(jsonify(message=response_message), 401))
            except AttributeError as e:
                flash(f'An error <{e}> occurred. Пожалйста, перезагрузите страницу или вернитесь на предыдущую.',
                      'danger')
                return decorated_route
        return decorated_route

    return decorator
