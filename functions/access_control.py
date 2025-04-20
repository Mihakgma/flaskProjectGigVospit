from functools import wraps
from flask import redirect, session, flash, url_for


# Сам декоратор проверки доступа
def role_required(*roles):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not session.get('user'):
                return redirect(url_for('auth.login'))  # перенаправляет на вход, если пользователь не вошел

            user_roles = session['user'].get('roles', [])  # получаем роли пользователя
            if any(role in roles for role in user_roles):
                print("access granted")
                return f(*args, **kwargs)
            else:
                flash("У вас недостаточно прав для доступа к этому ресурсу.")
                return redirect('/')

        return decorated_function

    return decorator
