import functools
from flask import abort, make_response, jsonify
from flask_login import current_user

from models import User
from utils.crud_classes import UserCrudControl


def role_required(*role_names):
    def decorator(original_route):
        @functools.wraps(original_route)
        def decorated_route(*args, **kwargs):
            user = User.query.filter_by(id=current_user.id).first()
            UserCrudControl.check_all_users_last_activity(current_user=user)
            if not current_user.is_authenticated or not user.is_logged_in:
                user_crud_control = UserCrudControl(user=user,
                                                    need_commit=True)
                user_crud_control.logout()
                abort(401, description="Пользователь не аутентифицирован")
            if current_user.status.code == "blocked" or current_user.status.code == "block":
                abort(401, description="Пользователь заблокирован")
            if "anyone" in role_names:
                return original_route(*args, **kwargs)
            roles = current_user.roles
            user_roles = {role.code for role in roles}
            if any(role_name in user_roles for role_name in role_names):
                return original_route(*args, **kwargs)
            response_message = f"ACCESS DENIED - REQUIRED ANY OF THESE ROLES: {', '.join(role_names)}"
            abort(make_response(jsonify(message=response_message), 401))

        return decorated_route

    return decorator
