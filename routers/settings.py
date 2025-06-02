# settings_bp.py (или расширьте ваш admin_bp.py)
from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from database import db
from models import AccessSetting, User  # Убедитесь, что AccessSetting и db импортированы
from forms.forms import AccessSettingForm  # Убедитесь, что AccessSettingForm импортирована
from functions.access_control import role_required  # Ваш декоратор role_required
from utils.crud_classes import UserCrudControl
from utils.pages_lock.lock_management import PageLocker

# Создаем Blueprint для настроек
settings_bp = Blueprint('settings', __name__, url_prefix='/settings')


# 1) Роут для отображения списка всех записей таблицы БД
@settings_bp.route('/')
@login_required
@role_required('admin')
def list_settings():
    """
    Отображает список всех существующих настроек программы.
    """
    settings = AccessSetting.query.order_by(AccessSetting.id).all()
    # Получаем текущую активную настройку для отображения
    active_setting = AccessSetting.get_activated_setting()
    return render_template('settings/list_settings.html', settings=settings, active_setting_id=active_setting.id if active_setting else None)


# Роут для добавления новой настройки
@settings_bp.route('/new', methods=['GET', 'POST'])
@login_required
@role_required('super', 'admin', 'moder')
def create_setting():
    """
    Обрабатывает создание новой настройки программы.
    """
    form = AccessSettingForm()
    if form.validate_on_submit():
        try:
            new_setting = AccessSetting(
                name=form.name.data,
                page_lock_seconds=form.page_lock_seconds.data,
                activity_timeout_seconds=form.activity_timeout_seconds.data,
                max_admins_number=form.max_admins_number.data,
                max_moders_number=form.max_moders_number.data,
                activity_period_counter=form.activity_period_counter.data,
                activity_counter_max_threshold=form.activity_counter_max_threshold.data,
                is_activated_now=False # Новые настройки по умолчанию не активны
            )
            db.session.add(new_setting)
            db.session.commit()
            flash('Настройка успешно создана!', 'success')
            return redirect(url_for('settings.list_settings'))
        except Exception as e:
            db.session.rollback()
            flash(f'Ошибка при создании настройки: {e}', 'error')
    elif request.method == 'POST': # Если форма не прошла валидацию при POST запросе
        for field, errors in form.errors.items():
            for error in errors:
                flash(f"Ошибка в поле '{form[field].label.text}': {error}", 'error')

    return render_template('settings/create_setting.html', form=form)


# Роут для активации настройки (используется AJAX)
@settings_bp.route('/activate/<int:setting_id>', methods=['POST'])
@login_required
@role_required('super')
def activate_setting(setting_id):
    """
    Активирует выбранную настройку программы.
    Использует слушатель SQLAlchemy для деактивации других настроек.
    """
    setting_to_activate = AccessSetting.query.get(setting_id)
    if not setting_to_activate:
        return jsonify({'status': 'error', 'message': 'Настройка не найдена.'}), 404

    try:
        # Устанавливаем is_activated_now в True.
        # Слушатель before_update деактивирует остальные.
        # Если setting_to_activate уже активна, это все равно сработает,
        # но слушатель ничего не изменит в БД для других, т.к. их нет.
        # db.session.commit() здесь вызовет слушателя.
        setting_to_activate.is_activated_now = True
        db.session.commit()
        # После коммита, если слушатель сработал,
        # у нас будет только одна активная запись.
        flash('Настройка успешно активирована!', 'success')
        return jsonify({'status': 'success', 'message': 'Настройка успешно активирована!'})

    except Exception as e:
        db.session.rollback()
        # Если здесь произошло IntegrityError из-за DB-уровня UniqueConstraint,
        # это значит, что слушатель не сработал или был перехвачен ранее.
        # Пользователь увидит сообщение об ошибке.
        flash(f'Ошибка при активации настройки: {e}', 'error')
        return jsonify({'status': 'error', 'message': f'Ошибка при активации настройки: {e}'}), 500


# Роут для удаления настройки
@settings_bp.route('/delete/<int:setting_id>', methods=['POST'])
@login_required
@role_required('super')
def delete_setting(setting_id):
    """
    Удаляет выбранную настройку программы.
    Если удаляется активная настройка, активирует первую в списке (с наименьшим ID).
    """
    setting_to_delete = AccessSetting.query.get(setting_id)
    if not setting_to_delete:
        flash('Настройка не найдена.', 'error')
        return redirect(url_for('settings.list_settings'))

    is_deleted_setting_active = setting_to_delete.is_activated_now

    try:
        db.session.delete(setting_to_delete)
        db.session.commit()
        flash('Настройка успешно удалена!', 'success')

        # Если удаленная настройка была активной, то активируем первую оставшуюся
        if is_deleted_setting_active:
            # Находим первую настройку по возрастанию ID
            remaining_settings = AccessSetting.query.order_by(AccessSetting.id).first()
            if remaining_settings:
                # Наш слушатель before_update позаботится о том, чтобы другие стали False
                remaining_settings.is_activated_now = True
                db.session.commit() # Отдельный коммит для активации новой
                flash(f'Удаленная настройка была активной. Новая активная настройка: "{remaining_settings.name}".', 'info')
            else:
                flash('Все настройки удалены. Активных настроек больше нет.', 'warning')

    except Exception as e:
        db.session.rollback()
        flash(f'Ошибка при удалении настройки: {e}', 'error')

    return redirect(url_for('settings.list_settings'))


# Новый роут для сброса сессий всех пользователей
@settings_bp.route('/restart_all_sessions', methods=['POST'])
@login_required
@role_required('admin') # Или отдельная роль, если нужна более гранулярная настройка
def restart_all_sessions():
    """
    Разлогинивает всех пользователей, перезапуская их сессии.
    """
    try:
        users = User.query.all() # Получаем всех пользователей
        UserCrudControl.sessions_restart(db_obj=db, users=users, need_commit=True)
        flash('Все пользовательские сессии успешно сброшены!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Ошибка при сбросе сессий: {e}', 'error')
    return redirect(url_for('settings.list_settings'))


# Новый роут для разблокировки всех страниц
@settings_bp.route('/clear_all_locks', methods=['POST'])
@login_required
@role_required('admin') # Или отдельная роль
def clear_all_locks():
    """
    Разблокирует все редактируемые на данный момент страницы.
    """
    try:
        PageLocker.clear_locked_pages()
        db.session.commit() # Если clear_locked_pages изменяет БД, нужно commit
        flash('Все заблокированные страницы успешно разблокированы!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Ошибка при разблокировке страниц: {e}', 'error')
    return redirect(url_for('settings.list_settings'))