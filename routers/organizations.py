from flask import (Blueprint,
                   render_template,
                   redirect,
                   url_for,
                   flash,
                   jsonify,
                   request)
from flask_login import login_required
from sqlalchemy.sql.functions import func

from functions.access_control import role_required
from models.models import Organization
from database import db

from sqlalchemy.exc import IntegrityError

from forms.forms import OrganizationAddForm

orgs_bp = Blueprint('organizations', __name__)  # Создаем blueprint


@orgs_bp.route('/add', methods=['GET', 'POST'])
@login_required
@role_required('admin', 'moder', 'oper', )
def add_organization():
    form = OrganizationAddForm()

    if form.validate_on_submit():
        try:
            org = Organization(
                name=form.name.data,
                inn=form.inn.data,
                address=form.address.data,
                phone_number=form.phone_number.data,
                email=form.email.data,
                is_active=form.is_active.data,
                additional_info=form.additional_info.data
            )
            db.session.add(org)
            db.session.commit()
            flash('Организация успешно добавлена!', 'success')
            return redirect(url_for('routes.organization_details',
                                    organization_id=org.id))

        except IntegrityError as e:
            db.session.rollback()
            if 'UNIQUE constraint failed' in str(e):
                if 'inn' in str(e):
                    flash('Организация с таким ИНН уже существует.', 'danger')
                else:  # Для других потенциальных уникальных полей
                    flash('Произошла ошибка, связанная с уникальностью данных. Проверьте введённую информацию.',
                          'danger')
            else:
                print(f"Ошибка при добавлении организации: {e}")
                flash('Произошла ошибка при добавлении организации. Попробуйте позже.', 'danger')

        except Exception as e:
            db.session.rollback()
            print(f"Ошибка при добавлении организации: {e}")
            flash('Произошла ошибка при добавлении организации. Попробуйте позже.', 'danger')
    return render_template('add_organization.html',
                           form=form,
                           title="Добавить организацию")


@orgs_bp.route('/details/<int:organization_id>')
@login_required
@role_required('anyone')
def organization_details(organization_id):
    organization = Organization.query.get_or_404(organization_id)
    return render_template('organization_details.html',
                           organization=organization,
                           title="Детали организации")


@orgs_bp.route('/search')
@login_required
@role_required('admin', 'moder', 'oper', )
def search_organizations():
    q = request.args.get('q')
    page = int(request.args.get('page', 1))

    organizations = Organization.query.filter(Organization.name.ilike(f"%{q}%")).paginate(page=page, per_page=30,
                                                                                          error_out=False)
    # work with sqlite3 db
    if organizations.total == 0:
        print("sqlite3 db detected!")
        organizations = Organization.query.filter(
            func.upper(Organization.name).like(f"%{q.upper()}%")  # или lower() для обоих
        ).paginate(page=page, per_page=30, error_out=False)

    return jsonify({
        'items': [{'id': org.id, 'text': org.name} for org in organizations.items],
        'total_count': organizations.total
    })


@orgs_bp.route('/check_inn')
def check_inn():
    inn = request.args.get('inn')
    organization = Organization.query.filter_by(inn=inn).first()
    return jsonify({'exists': organization is not None})
