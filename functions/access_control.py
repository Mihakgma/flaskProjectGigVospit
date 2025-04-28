import functools
from flask import abort, make_response, jsonify
from flask_login import current_user


def role_required(*role_names):
    def decorator(original_route):
        @functools.wraps(original_route)
        def decorated_route(*args, **kwargs):
            if not current_user.is_authenticated:
                abort(401, description="Пользователь не аутентифицирован")

            # Получаем роли пользователя
            roles = current_user.roles
            # Набор существующих ролей пользователя
            user_roles = {role.code for role in roles}

            # Допускаем пользователя, если у него есть хотя бы одна нужная роль
            if any(role_name in user_roles for role_name in role_names):
                return original_route(*args, **kwargs)

            # Формируем сообщение об отсутствии необходимых прав
            response_message = f"ACCESS DENIED - REQUIRED ANY OF THESE ROLES: {', '.join(role_names)}"
            abort(make_response(jsonify(message=response_message), 401))

        return decorated_route

    return decorator
