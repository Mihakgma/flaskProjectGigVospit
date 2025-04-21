# from functools import wraps
# from flask import redirect, session, flash, url_for
import functools
from flask import abort
from flask_login import current_user


# Сам декоратор проверки доступа
def role_required(*role_names):
    def decorator(original_route):
        @functools.wraps(original_route)
        def decorated_route(*args, **kwargs):
            if not current_user.is_authenticated:
                abort(401)
            print(current_user.roles.__dict__.keys())

            user_roles = set(current_user.roles.codes)
            missing_roles = set(role_names) - user_roles

            if missing_roles:
                abort(401, message="Missing role(s): {}".format(', '.join(missing_roles)))

            return original_route(*args, **kwargs)

        return decorated_route

    return decorator
