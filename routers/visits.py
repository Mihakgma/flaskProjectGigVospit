# visits.py

from flask import Blueprint, render_template, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from database import db
from forms.forms import EditVisitForm
from models.models import Vizit
from functions.access_control import role_required
from utils.pages_lock.lock_info import LockInfo
from utils.pages_lock.lock_management import PageLocker

visits_bp = Blueprint('visits', __name__)


@visits_bp.route('/visit/<int:visit_id>/edit', methods=['GET', 'POST'])
@login_required
@role_required('super', 'admin', 'moder', 'oper')  # Укажите необходимые роли
def edit_visit(visit_id):
    timeout = PageLocker.get_timeout()
    print(f'Timeout: {timeout} secs...')
    lock_info = LockInfo("visits_bp",
                         "edit_visit",
                         visit_id,
                         current_user.id)
    visit = Vizit.query.get_or_404(visit_id)
    if PageLocker.lock_page(lock_data=lock_info):
        flash(f'У Вас есть <{timeout}> секунд на редактирование '
              f'и сохранение изменений для текущей страницы...', 'warning')

        # Инициализируем форму существующими данными визита
        # WTForms автоматически заполнит поля формы значениями из объекта `visit`
        # при условии, что имена полей формы совпадают с атрибутами объекта `visit`.
        form = EditVisitForm(obj=visit)

        if form.validate_on_submit():
            # Обновляем поля визита данными из формы
            # populate_obj корректно работает как для SelectField (по ID), так и для QuerySelectField (по объекту)
            form.populate_obj(visit)
            try:
                db.session.commit()
                flash('Визит успешно обновлен!', 'success')
                PageLocker.unlock_page(lock_data=lock_info)
                # Перенаправляем обратно на страницу деталей заявителя
                return redirect(url_for('applicants.applicant_details', applicant_id=visit.applicant_id))
            except Exception as e:
                db.session.rollback()
                flash(f'Ошибка при обновлении визита: {e}', 'error')

        # Для GET-запроса или при ошибке валидации, форма будет отображаться с текущими данными
        return render_template('visits/edit_visit.html',
                               form=form,
                               visit=visit,
                               timeout=timeout)
    else:
        # Перенаправляем обратно на страницу деталей заявителя
        return redirect(url_for('applicants.applicant_details',
                                applicant_id=visit.applicant_id))


# --- Роут для удаления визита (через AJAX/fetch) ---
@visits_bp.route('/visit/<int:visit_id>/delete', methods=['POST'])
@login_required
@role_required('super', 'admin', 'moder')  # Укажите необходимые роли
def delete_visit(visit_id):
    visit = Vizit.query.get_or_404(visit_id)
    applicant_id = visit.applicant_id  # Сохраняем ID заявителя для перенаправления

    try:
        db.session.delete(visit)
        db.session.commit()
        flash(f'Визит от {visit.visit_date.strftime("%d.%m.%Y")} успешно удален!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Ошибка при удалении визита: {e}', 'error')

    # Всегда перенаправляем обратно на страницу редактирования заявителя
    return redirect(url_for('applicants.edit_applicant', applicant_id=applicant_id))
