# project/routes/backup_settings.py
from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required  # Если используете Flask-Login
# from flask_login import current_user # Если нужны роли
from database import db
from forms.forms import BackupSettingForm
from functions.access_control import role_required
from models import BackupSetting  # Ваша модель BackupSetting

backup_settings_bp = Blueprint('backup_settings', __name__)


@backup_settings_bp.route('/', defaults={'setting_id': None}, methods=['GET', 'POST'])
@backup_settings_bp.route('/<int:setting_id>', methods=['GET', 'POST'])  # Для редактирования по ID
@login_required
@role_required('super')  # Укажите необходимые роли
def manage_backup_settings(setting_id):
    setting_to_edit = None
    if setting_id:
        setting_to_edit = BackupSetting.query.get_or_404(setting_id)
        form = BackupSettingForm(obj=setting_to_edit)  # Заполнение формы данными для редактирования
    else:
        form = BackupSettingForm()  # Пустая форма для создания новой настройки

    if request.method == 'POST':
        # Определяем тип POST-запроса через скрытое поле form_type
        form_type = request.form.get('form_type')

        if form_type == 'create_edit':
            # Проверяем валидацию формы
            if form.validate_on_submit():
                if setting_to_edit:  # Редактирование существующей настройки
                    form.populate_obj(setting_to_edit)
                    # is_active_now не изменяется через эту форму
                    try:
                        db.session.commit()
                        flash(f'Настройка "{setting_to_edit.name}" успешно обновлена!', 'success')
                        return redirect(url_for('backup_settings.manage_backup_settings'))
                    except Exception as e:
                        db.session.rollback()
                        flash(f'Ошибка при обновлении настройки: {e}', 'danger')
                else:  # Создание новой настройки
                    new_setting = BackupSetting()
                    form.populate_obj(new_setting)
                    new_setting.is_active_now = False  # Новые настройки не активны по умолчанию
                    try:
                        db.session.add(new_setting)
                        db.session.commit()
                        flash(f'Настройка "{new_setting.name}" успешно добавлена!', 'success')
                        return redirect(url_for('backup_settings.manage_backup_settings'))
                    except Exception as e:
                        db.session.rollback()
                        # Обработка ошибки, например, при дублировании имени
                        if "IntegrityError" in str(e):  # Более точная проверка, если есть уникальное ограничение
                            flash(f'Ошибка: Настройка с именем "{new_setting.name}" уже существует.', 'danger')
                        else:
                            flash(f'Ошибка при добавлении настройки: {e}', 'danger')
            else:
                # Валидация формы не пройдена, отображаем ошибки
                for field, errors in form.errors.items():
                    for error in errors:
                        flash(f'Ошибка в поле "{form[field].label.text}": {error}', 'danger')
                # Важно: если валидация не прошла, нужно снова отрендерить страницу
                # с текущими данными формы и ошибками.
                settings = BackupSetting.query.order_by(BackupSetting.id).all()
                return render_template('backup/backup_settings.html', form=form, settings=settings,
                                       current_setting=setting_to_edit)

        elif form_type == 'activate':
            setting_id_to_activate = request.form.get('setting_id')
            if setting_id_to_activate:
                try:
                    selected_setting = BackupSetting.query.get_or_404(setting_id_to_activate)

                    # Деактивируем все остальные настройки
                    # synchronize_session=False важен для bulk-обновлений, чтобы избежать ошибок
                    db.session.query(BackupSetting).filter(
                        BackupSetting.id != selected_setting.id,
                        BackupSetting.is_active_now == True
                    ).update({BackupSetting.is_active_now: False}, synchronize_session=False)

                    # Активируем выбранную настройку
                    selected_setting.is_active_now = True
                    db.session.commit()
                    flash(f'Настройка "{selected_setting.name}" успешно активирована!', 'success')
                except Exception as e:
                    db.session.rollback()
                    flash(f'Ошибка при активации настройки: {e}', 'danger')
            else:
                flash('Неверный ID настройки для активации.', 'danger')
            return redirect(url_for('backup_settings.manage_backup_settings'))  # Перенаправление после действия

        elif form_type == 'delete':
            setting_id_to_delete = request.form.get('setting_id')
            if setting_id_to_delete:
                try:
                    setting_to_delete = BackupSetting.query.get_or_404(setting_id_to_delete)
                    setting_name = setting_to_delete.name

                    is_deleted_setting_active = setting_to_delete.is_active_now

                    db.session.delete(setting_to_delete)
                    db.session.commit()  # Сначала коммитим удаление

                    if is_deleted_setting_active:
                        # Если удаляемая настройка была активной, активируем первую попавшуюся
                        remaining_settings = BackupSetting.query.order_by(BackupSetting.id).first()
                        if remaining_settings:
                            remaining_settings.is_active_now = True
                            db.session.commit()  # Коммитим активацию
                            flash(
                                f'Настройка "{setting_name}" удалена. Активной сделана настройка: "{remaining_settings.name}".',
                                'success')
                        else:
                            flash(f'Настройка "{setting_name}" удалена. Активных настроек больше нет.', 'info')
                    else:  # Если удаляемая настройка была неактивной, просто удаляем
                        flash(f'Настройка "{setting_name}" успешно удалена!', 'success')

                except Exception as e:
                    db.session.rollback()
                    flash(f'Ошибка при удалении настройки: {e}', 'danger')
            else:
                flash('Неверный ID настройки для удаления.', 'danger')
            return redirect(url_for('backup_settings.manage_backup_settings'))  # Перенаправление после действия

    # Для GET-запроса или после неудачной POST-валидации (если не было редиректа)
    settings = BackupSetting.query.order_by(BackupSetting.id).all()
    return render_template('backup/backup_settings.html', form=form, settings=settings, current_setting=setting_to_edit)
