from datetime import datetime

from flask import (Blueprint,
                   render_template,
                   request,
                   redirect,
                   url_for,
                   flash, jsonify)
from flask_login import login_required
from sqlalchemy.orm import load_only, joinedload
from wtforms.validators import ValidationError

from functions.access_control import role_required
from models.models import Contract, Organization, Vizit
from database import db

from forms.forms import ContractForm

contracts_bp = Blueprint('contracts', __name__)


@contracts_bp.route('/add', methods=['GET', 'POST'])
@login_required
@role_required('admin', 'moder', 'oper', )
def add_contract():
    form = ContractForm()

    if request.method == 'POST':
        if form.validate_on_submit():
            try:
                form.check_duplicates()
                new_contract = Contract(
                    number=form.number.data,
                    contract_date=form.contract_date.data,
                    name=form.name.data,
                    expiration_date=form.expiration_date.data,
                    is_extended=form.is_extended.data,
                    organization_id=form.organization_id.data,  # Присваиваем выбранную организацию
                    info=form.info.data
                )
                db.session.add(new_contract)
                db.session.commit()
                flash('Новый контракт успешно добавлен!', 'success')
                return redirect(url_for('contract_details', contract_id=new_contract.id))
            except ValidationError as e:
                db.session.rollback()
                # flash(e)
                flash('Договор уже добавлен в БД.'
                      'Пожалуйста, попробуйте внести другой номер, дату подписания или организацию.')
            except Exception as e:
                db.session.rollback()
                print(f"Ошибка при добавлении контракта: {e}")
                flash('Произошла ошибка при добавлении контракта. Попробуйте позже.', 'danger')

    return render_template('add_contract.html', form=form)


@contracts_bp.route('/details/<int:contract_id>')
@login_required
@role_required('anyone')
def contract_details(contract_id):
    contract = Contract.query.options(
        joinedload(Contract.organization)  # Если есть связь с организацией
    ).get_or_404(contract_id)

    related_vizits_list = Vizit.query.filter_by(contract_id=contract.id).all()

    # 2. Количество визитов, к которым прикреплен текущий контракт
    num_related_vizits = len(related_vizits_list)

    # 3. Количество уникальных заявителей, к визитам которых прикреплен текущий контракт
    unique_applicant_ids = set()
    if related_vizits_list:  # Проверяем, что список не пуст
        for vizit in related_vizits_list:
            if vizit.applicant_id:  # Убедимся, что у визита есть заявитель
                unique_applicant_ids.add(vizit.applicant_id)

    num_unique_applicants = len(unique_applicant_ids)

    return render_template('contract_details.html',  # Имя вашего шаблона деталей контракта
                           contract=contract,
                           num_related_vizits=num_related_vizits,
                           num_unique_applicants=num_unique_applicants)


@contracts_bp.route('/search', methods=['GET'])
@login_required
@role_required('admin', 'moder', 'oper')
def search_contracts():
    q = request.args.get('q')  # Название организации
    page = int(request.args.get('page', 1))
    start_date = request.args.get('start_date')  # Дата подписания (от)
    end_date = request.args.get('end_date')  # Дата подписания (до)
    expiration_start_date = request.args.get('expiration_start_date')
    expiration_end_date = request.args.get('expiration_end_date')
    contract_name = request.args.get('contract_name')

    try:
        if start_date:
            start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
        if end_date:
            end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
        if expiration_start_date:
            expiration_start_date = datetime.strptime(expiration_start_date, '%Y-%m-%d').date()
        if expiration_end_date:
            expiration_end_date = datetime.strptime(expiration_end_date, '%Y-%m-%d').date()
    except ValueError:
        return jsonify({'error': 'Неверный формат даты'}), 400

    query = Contract.query.options(load_only(
        Contract.id,
        Contract.number,
        Contract.name,
        Contract.contract_date,
        Contract.expiration_date,
        Contract.is_extended,
        Contract.organization_id,
        Contract.info
    ))

    if q:  # Поиск по названию организации
        query = query.join(Organization).filter(Organization.name.ilike(f"%{q}%"))

    if start_date:
        query = query.filter(Contract.contract_date >= start_date)

    if end_date:
        query = query.filter(Contract.contract_date <= end_date)

    if expiration_start_date:
        query = query.filter(Contract.expiration_date >= expiration_start_date)

    if expiration_end_date:
        query = query.filter(Contract.expiration_date <= expiration_end_date)

    if contract_name:
        query = query.filter(Contract.name.ilike(f"%{contract_name}%"))

    contracts = query.paginate(page=page, per_page=30, error_out=False)

    results = []
    for contract in contracts.items:
        org_name = None
        if contract.organization_id:
            org = Organization.query.get(contract.organization_id)
            if org:
                org_name = org.name

        results.append({
            'id': contract.id,
            'number': contract.number,
            'name': contract.name,
            'organization_name': org_name,
            'contract_date': contract.contract_date.isoformat() if contract.contract_date else None,
            'expiration_date': contract.expiration_date.isoformat() if contract.expiration_date else None,
            'detail_url': f'/contracts/{contract.id}'
        })

    return render_template('search_contracts.html',
                           contracts=results,
                           total_count=contracts.total)
