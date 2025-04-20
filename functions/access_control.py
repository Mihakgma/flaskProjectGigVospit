from functools import wraps
from flask import redirect, session, flash


def role_required(*roles):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # Проверяем наличие пользователя в сессии
            if not session.get('user'):
                return redirect('/auth/login')

            user_roles = session['user'].get('roles', [])
            if any(role in roles for role in user_roles):
                return f(*args, **kwargs)
            else:
                flash("У вас недостаточно прав для доступа к этому ресурсу.")
                return redirect('/')

        return decorated_function

    return decorator
