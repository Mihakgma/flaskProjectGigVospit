from flask import (Blueprint,
                   render_template,
                   request,
                   redirect,
                   url_for,
                   flash)
from flask_login import login_required

from functions.access_control import role_required
from models.models import (Applicant,
                           Vizit)
from database import db

from datetime import timezone

from forms.forms import (AddApplicantForm,
                         VizitForm)

applicants_bp = Blueprint('applicants', __name__)  # Создаем blueprint


@applicants_bp.route('/add', methods=['GET', 'POST'])
@login_required
@role_required('admin', 'moder', 'oper', )
def add_applicant():
    applicant_form = AddApplicantForm()
    vizit_form = VizitForm()

    if request.method == 'POST':
        if applicant_form.validate_on_submit():  # Валидация формы заявителя
            try:
                new_applicant = Applicant()
                applicant_form.populate_obj(new_applicant)
                db.session.add(new_applicant)
                db.session.flush()

                if vizit_form.validate_on_submit():  # Валидация формы визита
                    new_vizit = Vizit()
                    vizit_form.populate_obj(new_vizit)
                    new_vizit.applicant_id = new_applicant.id
                    new_vizit.created_at = vizit_form.created_at.data
                    db.session.add(new_vizit)
                    new_applicant.vizits.append(new_vizit)

                db.session.commit()
                flash('Заявитель и визит (если был добавлен) успешно сохранены!', 'success')
                return redirect(url_for('applicants.applicant_details',
                                        applicant_id=new_applicant.id))

            except Exception as e:
                db.session.rollback()
                print(f"Ошибка при добавлении заявителя/визита: {e}")
                flash('Произошла ошибка при добавлении. Попробуйте позже.', 'danger')

        else:  # Если форма заявителя не валидна, проверяем и добавляем визит отдельно, если валиден
            if vizit_form.validate_on_submit():
                flash('Форма заявителя содержит ошибки. Пожалуйста исправьте их.', 'danger')

        # Выводим ошибки валидации формы заявителя, если они есть
        for field, errors in applicant_form.errors.items():
            for error in errors:
                flash(f"Ошибка в поле '{applicant_form[field].label.text}': {error}", 'danger')

    return render_template('add_applicant.html',
                           form=applicant_form,
                           vizit_form=vizit_form)


@applicants_bp.route('/details/<int:applicant_id>')
@login_required
@role_required('anyone')
def applicant_details(applicant_id):
    applicant = Applicant.query.get_or_404(applicant_id)
    return render_template('applicant_details.html',
                           applicant=applicant,
                           timezone=timezone)
