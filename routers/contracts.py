from flask import (Blueprint,
                   render_template,
                   request,
                   redirect,
                   url_for,
                   flash)
from flask_login import login_required

from functions.access_control import role_required
from models.models import Contract
from database import db

from forms.forms import AddContractForm

contracts_bp = Blueprint('contracts', __name__)  # Создаем blueprint


@contracts_bp.route('/add', methods=['GET', 'POST'])
@login_required
@role_required('admin', 'moder', 'oper', )
def add_contract():
    form = AddContractForm()

    if request.method == 'POST':
        if form.validate_on_submit():
            try:
                new_contract = Contract(
                    number=form.number.data,
                    contract_date=form.contract_date.data,
                    name=form.name.data,
                    expiration_date=form.expiration_date.data,
                    is_extended=form.is_extended.data,
                    organization_id=form.organization_id.data,  # Присваиваем выбранную организацию
                    additional_info=form.additional_info.data
                )

                # Подключаем выбранных заявителей к контракту
                # applicants = Applicant.query.filter(Applicant.id.in_(form.applicants.data)).all()
                # new_contract.applicants.extend(applicants)

                db.session.add(new_contract)
                db.session.commit()
                flash('Новый контракт успешно добавлен!', 'success')
                return redirect(url_for('contract_details', contract_id=new_contract.id))
            except Exception as e:
                db.session.rollback()
                print(f"Ошибка при добавлении контракта: {e}")
                flash('Произошла ошибка при добавлении контракта. Попробуйте позже.', 'danger')

    return render_template('add_contract.html', form=form)


@contracts_bp.route('/details/<int:contract_id>')
@login_required
@role_required('anyone')
def contract_details(contract_id):
    contract = Contract.query.get_or_404(contract_id)
    return render_template('contract_details.html', contract=contract)
