from flask import (Blueprint,
                   render_template,
                   request,
                   redirect,
                   url_for,
                   flash)

from models.models import (Applicant,
                           Contract,
                           Organization,
                           Vizit)
from database import db

from datetime import timezone
from sqlalchemy.exc import IntegrityError

from forms.forms import (AddApplicantForm,
                         AddContractForm,
                         OrganizationAddForm, VizitForm)

routes_bp = Blueprint('routes', __name__)  # Создаем blueprint

# Словарь с описанием роутов
ROUTES_INFO = [
    {'path': '/users/add',
     'title': 'Форма для добавления пользователя с ролями, отделом и статусом.',
     'route': 'users.add_user',
     },
    {'path': 'users/<int:user_id>',
     'title': 'Отображает детали пользователя.',
     # 'route': 'users.user_details'
     },
    {'path': '/applicants/add',
     'title': 'Добавить нового заявителя',
     'route': 'routes.add_applicant'
     },
    {'path': '/applicants/<int:applicant_id>',
     'title': 'Отображает детали заявителя',
     # 'route': 'routes.applicant_details',
     },
    {'path': '/organizations/add',
     'title': 'Добавление новой организации',
     'route': 'routes.add_organization'
     },
    {'path': '/organizations/<int:organization_id>',
     'title': 'Отображает детали организации',
     # 'route': 'routes.organization_details',
     },
    {'path': '/contracts/add',
     'title': 'Добавление нового контракта',
     'route': 'routes.add_contract'
     },
    {'path': '/contracts/<int:contract_id>',
     'title': 'Отображает детали контракта',
     },
    {'path': '/auth/register', 'title': 'Регистрация нового пользователя', 'route': 'auth.register'},
    {'path': '/auth/login', 'title': 'Войти в систему', 'route': 'auth.login'}
]


@routes_bp.route('/')
def index():
    return render_template('index.html', routes=ROUTES_INFO)


@routes_bp.route('/applicants/add', methods=['GET', 'POST'])
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
                return redirect(url_for('routes.applicant_details', applicant_id=new_applicant.id))

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

    return render_template('add_applicant.html', form=applicant_form, vizit_form=vizit_form)


@routes_bp.route('/applicants/<int:applicant_id>')
def applicant_details(applicant_id):
    applicant = Applicant.query.get_or_404(applicant_id)
    return render_template('applicant_details.html',
                           applicant=applicant,
                           timezone=timezone)


@routes_bp.route('/contracts/add', methods=['GET', 'POST'])
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


@routes_bp.route('/contracts/<int:contract_id>')
def contract_details(contract_id):
    contract = Contract.query.get_or_404(contract_id)
    return render_template('contract_details.html', contract=contract)


@routes_bp.route('/organizations/add', methods=['GET', 'POST'])
# @login_required
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


@routes_bp.route('/organizations/<int:organization_id>')
# @login_required
def organization_details(organization_id):
    organization = Organization.query.get_or_404(organization_id)
    return render_template('organization_details.html',
                           organization=organization,
                           title="Детали организации")
