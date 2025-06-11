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
        form = BackupSettingForm(obj=setting_to_edit)
    else:
        form = BackupSettingForm()

    if request.method == 'POST':
        form_type = request.form.get('form_type')

        if form_type == 'create_edit':
            if form.validate_on_submit():
                if setting_to_edit:
                    form.populate_obj(setting_to_edit)
                    try:
                        db.session.commit()
                        flash(f'Настройка "{setting_to_edit.name}" успешно обновлена!', 'success')
                        return redirect(url_for('backup_settings.manage_backup_settings'))
                    except Exception as e:
                        db.session.rollback()
                        if "IntegrityError" in str(e) and "name" in str(e):
                             flash(f'Ошибка: Настройка с именем "{setting_to_edit.name}" уже существует.', 'danger')
                        else:
                            flash(f'Ошибка при обновлении настройки: {e}', 'danger')
                else:
                    new_setting = BackupSetting()
                    form.populate_obj(new_setting)
                    new_setting.is_active_now = False
                    try:
                        db.session.add(new_setting)
                        db.session.commit()
                        flash(f'Настройка "{new_setting.name}" успешно добавлена!', 'success')
                        return redirect(url_for('backup_settings.manage_backup_settings'))
                    except Exception as e:
                        db.session.rollback()
                        if "IntegrityError" in str(e) and "name" in str(e):
                             flash(f'Ошибка: Настройка с именем "{new_setting.name}" уже существует.', 'danger')
                        else:
                            flash(f'Ошибка при добавлении настройки: {e}', 'danger')
            else:
                for field, errors in form.errors.items():
                    for error in errors:
                        flash(f'Ошибка в поле "{form[field].label.text}": {error}', 'danger')
                settings = BackupSetting.query.order_by(BackupSetting.id).all()
                return render_template('backup/backup_settings.html',
                                       form=form,
                                       settings=settings,
                                       current_setting=setting_to_edit)

        elif form_type == 'activate':
            setting_id_to_activate = request.form.get('setting_id')
            if setting_id_to_activate:
                try:
                    selected_setting = BackupSetting.query.get_or_404(setting_id_to_activate)

                    db.session.query(BackupSetting).filter(
                        BackupSetting.id != selected_setting.id,
                        BackupSetting.is_active_now == True
                    ).update({BackupSetting.is_active_now: False}, synchronize_session=False)

                    selected_setting.is_active_now = True
                    db.session.commit()
                    flash(f'Настройка "{selected_setting.name}" успешно активирована!', 'success')
                except Exception as e:
                    db.session.rollback()
                    flash(f'Ошибка при активации настройки: {e}', 'danger')
            else:
                flash('Неверный ID настройки для активации.', 'danger')
            return redirect(url_for('backup_settings.manage_backup_settings'))

        elif form_type == 'delete':
            setting_id_to_delete = request.form.get('setting_id')
            if setting_id_to_delete:
                try:
                    setting_to_delete = BackupSetting.query.get_or_404(setting_id_to_delete)
                    setting_name = setting_to_delete.name

                    is_deleted_setting_active = setting_to_delete.is_active_now

                    db.session.delete(setting_to_delete)
                    db.session.commit()

                    if is_deleted_setting_active:
                        remaining_settings = BackupSetting.query.order_by(BackupSetting.id).first()
                        if remaining_settings:
                            remaining_settings.is_active_now = True
                            db.session.commit()
                            flash(f'Настройка "{setting_name}" удалена. Активной сделана настройка: "{remaining_settings.name}".', 'success')
                        else:
                            flash(f'Настройка "{setting_name}" удалена. Активных настроек больше нет.', 'info')
                    else:
                        flash(f'Настройка "{setting_name}" успешно удалена!', 'success')

                except Exception as e:
                    db.session.rollback()
                    if "ForeignKeyViolation" in str(e) or "IntegrityError" in str(e):
                        flash(f'Ошибка: Настройку "{setting_name}" нельзя удалить, '
                              f'так как с ней связаны записи в логах бэкапа.', 'danger')
                    else:
                        flash(f'Ошибка при удалении настройки: {e}', 'danger')
            else:
                flash('Неверный ID настройки для удаления.', 'danger')
            return redirect(url_for('backup_settings.manage_backup_settings'))

    settings = BackupSetting.query.order_by(BackupSetting.id).all()
    return render_template('backup/backup_settings.html',
                           form=form,
                           settings=settings,
                           current_setting=setting_to_edit)