import functools
from flask import flash, redirect, url_for, request  # request не использовался, но полезен
from flask_login import current_user, logout_user

from database import db  # Убедитесь, что db импортирован
from models import User  # Убедитесь, что User импортирован
from utils.crud_classes import UserCrudControl  # Ваш UserCrudControl
from models.models import get_current_nsk_time  # Убедитесь, что эта функция доступна
from functions import get_ip_address  # Убедитесь, что эта функция доступна


def role_required(*role_names):
    def decorator(original_route):
        @functools.wraps(original_route)
        def decorated_route(*args, **kwargs):
            # 1. ПЕРВАЯ ПРОВЕРКА: Статус аутентификации Flask-Login.
            if not current_user.is_authenticated:
                flash('Вы не авторизованы. Пожалуйста, войдите, чтобы получить доступ.', 'warning')
                return redirect(url_for('auth.login'))  # 2. Получаем актуальный объект пользователя из базы данных.
            user_from_db = db.session.get(User, current_user.id)
            if current_user.is_authenticated and not user_from_db.is_logged_in:
                flash('Вы не авторизованы. Пожалуйста, войдите, чтобы получить доступ.', 'warning')
                return redirect(url_for('auth.login'))
            # 3. Если пользователь не найден в БД (был удален).
            elif not user_from_db:
                flash('Ваш аккаунт не найден или был удален. Пожалуйста, войдите снова.', 'danger')
                logout_user()
                return redirect(url_for('auth.login'))
            # 5. Проверка статуса блокировки пользователя.
            elif user_from_db.status.code == "blocked" or user_from_db.status.code == "block":
                flash('Ваш аккаунт заблокирован. Свяжитесь с администратором.', 'danger')
                logout_user()
                user_crud = UserCrudControl(user=user_from_db,
                                            need_commit=True,
                                            db_object=db)
                user_crud.logout()
                return redirect(url_for('auth.login'))
            # 4. Синхронизируем статус is_logged_in в БД.
            # ЭТОТ БЛОК РАЗЛОГИНИВАЕТ current_user, ЕСЛИ НЕ УДАЕТСЯ СОХРАНИТЬ ЕГО СТАТУС В БД.
            elif not user_from_db.is_logged_in:
                user_from_db.is_logged_in = True
                user_from_db.logged_in_at = get_current_nsk_time()
                user_from_db.valid_ip = get_ip_address()
                try:
                    # ДОБАВЛЕНО: Убедимся, что объект отслеживается сессией.
                    db.session.add(user_from_db)
                    db.session.commit()
                    flash(f'Ваша сессия восстановлена, {user_from_db.username}.', 'info')
                except Exception as e:
                    db.session.rollback()
                    print(f"ERROR: Не удалось восстановить статус логина для пользователя {user_from_db.username}: {e}")
                    flash(f'Произошла ошибка при восстановлении сессии. Пожалуйста, попробуйте еще раз.', 'danger')
                    logout_user()  # Намеренный разлогин, если синхронизация не удалась
                    return redirect(url_for('auth.login'))

            # 6. Обновляем время последней активности текущего пользователя и проверяем других.
            UserCrudControl.check_all_users_last_activity(current_user=user_from_db)

            # 7. Проверка ролей.
            if "anyone" in role_names:
                return original_route(*args, **kwargs)

            user_roles = {role.code for role in user_from_db.roles} if user_from_db.roles else set()

            if any(role_name in user_roles for role_name in role_names):
                return original_route(*args, **kwargs)

            # 8. Если роли не соответствуют - Доступ запрещен.
            response_message = f"ДОСТУП ЗАПРЕЩЕН - ТРЕБУЮТСЯ СЛЕДУЮЩИЕ РОЛИ: {', '.join(role_names)}"
            flash(response_message, 'danger')
            # Перенаправляем на безопасную страницу. 'routes.index' должен быть доступен всем!
            return redirect(url_for('routes.index'))

        return decorated_route

    return decorator
