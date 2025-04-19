from flask import (Blueprint,
                   render_template,
                   jsonify,
                   request,
                   redirect,
                   url_for,
                   flash)
from models.models import (User,
                           Role,
                           Department,
                           Status,
                           Applicant,
                           Contingent,
                           WorkField,
                           ApplicantType,
                           AttestationType,
                           Contract, Organization)
from database import db

from werkzeug.security import generate_password_hash
from datetime import datetime
from sqlalchemy.exc import IntegrityError

from routers.forms import AddApplicantForm, AddContractForm

routes_bp = Blueprint('routes', __name__)  # Создаем blueprint

# Словарь с описанием роутов
ROUTES_INFO = {
    '/hello/<name>': 'Пример роута с параметром. Отображает приветствие с именем.',
    '/data': 'Возвращает JSON данные.',
    '/submit': 'Обрабатывает POST запрос и отображает введенные данные.',
    '/new_user': 'Создает нового пользователя (упрощенный вариант).',
    '/users/add': 'Форма для добавления пользователя с ролями, отделом и статусом.',
    '/users/<int:user_id>': 'Отображает детали пользователя.',
    '/applicants/add': 'Добавить нового заявителя',
    '/applicants/<int:applicant_id>': 'Отображает детали заявителя'
}


@routes_bp.route('/')
def index():
    return render_template('index.html', routes=ROUTES_INFO)


@routes_bp.route('/hello/<name>')
def hello(name):
    return render_template('hello.html', name=name)


@routes_bp.route('/data')
def data():
    return jsonify({'ключ': 'значение'})


@routes_bp.route('/submit', methods=['POST'])
def submit():
    name = request.form['name']
    return f'Введенные Вами данные: <{name}>'


@routes_bp.route('/new_user', methods=['POST'])
def new_user():
    try:
        name = request.form['user_name']
        email = request.form['user_email']
        new_user = User(username=name, email=email)
        db.session.add(new_user)
        db.session.commit()
        return jsonify(new_user.dict), 201  # Код 201 Created
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@routes_bp.route('/users/add', methods=['GET', 'POST'])
def add_user():
    if request.method == 'POST':
        try:
            # Получаем все поля из формы
            first_name = request.form.get('first_name')
            last_name = request.form.get('last_name')
            middle_name = request.form.get('middle_name')
            username = request.form.get('username')
            email = request.form.get('email')
            password = request.form.get('password')
            phone = request.form.get('phone')
            role_ids = request.form.getlist('role_id')  # Список выбранных ролей
            dept_id = request.form.get('dept_id')
            status_id = request.form.get('status_id')

            # Проверка уникальности имени пользователя и адреса электронной почты
            existing_username = User.query.filter_by(username=username).first()
            existing_email = User.query.filter_by(email=email).first()

            if existing_username or existing_email:
                error_message = ''
                if existing_username:
                    error_message += f'Пользователь с именем {username} уже существует.<br>'
                if existing_email:
                    error_message += f'Адрес электронной почты {email} уже используется.<br>'

                flash(error_message, 'danger')
                return render_template('add_user.html',
                                       first_name=first_name,
                                       last_name=last_name,
                                       middle_name=middle_name,
                                       username=username,
                                       email=email,
                                       phone=phone,
                                       dept_id=dept_id,
                                       status_id=status_id)

            hashed_password = generate_password_hash(password, method='pbkdf2:sha256')

            new_user = User(
                first_name=first_name,
                last_name=last_name,
                middle_name=middle_name,
                username=username,
                email=email,
                password=hashed_password,
                phone=phone,
                dept_id=dept_id,
                status_id=status_id
            )

            # Добавляем роли к пользователю
            roles = Role.query.filter(Role.id.in_(role_ids)).all()
            new_user.roles.extend(roles)

            db.session.add(new_user)
            db.session.commit()
            flash('Новый пользователь успешно добавлен!', 'success')
            return redirect(url_for('routes.user_details', user_id=new_user.id))

        except IntegrityError as e:
            db.session.rollback()
            flash(f'Ошибка целостности данных: {str(e)}', 'danger')
            return render_template('add_user.html')

        except Exception as e:
            db.session.rollback()
            return jsonify({'error': str(e)}), 500

    roles = Role.query.all()
    departments = Department.query.all()
    statuses = Status.query.all()
    return render_template('add_user.html',
                           roles=roles,
                           departments=departments,
                           statuses=statuses)


@routes_bp.route('/users/<int:user_id>')
def user_details(user_id):
    user = User.query.get_or_404(user_id)
    return render_template('user_details.html', user=user)


@routes_bp.route('/applicants/add', methods=['GET', 'POST'])
def add_applicant():
    form = AddApplicantForm()

    # Запросы к базе данных для select полей (ОБЯЗАТЕЛЬНО ПРОВЕРЬТЕ НАЛИЧИЕ ДАННЫХ):
    contingents = Contingent.query.all()
    work_fields = WorkField.query.all()
    applicant_types = ApplicantType.query.all()
    attestation_types = AttestationType.query.all()
    users = User.query.all()  # Это нужно для выбора пользователя, если требуется

    form.contingent_id.choices = [(c.id, c.name) for c in contingents]
    form.work_field_id.choices = [(w.id, w.name) for w in work_fields]
    form.applicant_type_id.choices = [(a.id, a.name) for a in applicant_types]
    form.attestation_type_id.choices = [(at.id, at.name) for at in attestation_types]

    if request.method == 'POST':
        if form.validate_on_submit():
            try:
                new_applicant = Applicant(
                    first_name=form.first_name.data,
                    last_name=form.last_name.data,
                    middle_name=form.middle_name.data,
                    medbook_number=form.medbook_number.data,
                    snils_number=form.snils_number.data,
                    passport_number=form.passport_number.data,
                    birth_date=form.birth_date.data,
                    registration_address=form.registration_address.data,
                    residence_address=form.residence_address.data,
                    phone_number=form.phone_number.data,
                    email=form.email.data,
                    contingent_id=form.contingent_id.data,
                    work_field_id=form.work_field_id.data,
                    applicant_type_id=form.applicant_type_id.data,
                    attestation_type_id=form.attestation_type_id.data,
                    edited_time=datetime.utcnow(),
                    # edited_by_user_id=form.edited_by_user_id.data, # Не нужно, т.к. edited_by определяется автоматически
                    # is_editing_now = form.is_editing_now.data, # Не нужно устанавливать здесь
                    # editing_by_id = form.editing_by_id.data, # Не нужно устанавливать здесь
                    # editing_started_at = form.editing_started_at.data # Не нужно устанавливать здесь
                )
                db.session.add(new_applicant)
                db.session.commit()

                flash('Новый заявитель успешно добавлен!', 'success')
                return redirect(url_for('routes.applicant_details', applicant_id=new_applicant.id))

            except IntegrityError as e:
                db.session.rollback()
                if 'UNIQUE constraint failed' in str(e):
                    if 'medbook_number' in str(e):
                        flash('Заявитель с таким номером медкнижки уже существует.', 'danger')
                    elif 'snils_number' in str(e):
                        flash('Заявитель с таким СНИЛС уже существует.', 'danger')
                    else:  # Для других потенциальных уникальных полей
                        flash('Произошла ошибка, связанная с уникальностью данных. Проверьте введенную информацию.',
                              'danger')
                else:
                    print(f"Ошибка при добавлении заявителя: {e}")
                    flash('Произошла ошибка при добавлении заявителя. Попробуйте позже.', 'danger')

            except Exception as e:
                db.session.rollback()
                print(f"Ошибка при добавлении заявителя: {e}")
                flash('Произошла ошибка при добавлении заявителя. Попробуйте позже.', 'danger')

    return render_template('add_applicant.html',
                           form=form,
                           contingents=contingents,
                           work_fields=work_fields,
                           applicant_types=applicant_types,
                           attestation_types=attestation_types,
                           users=users  # Если требуется для других целей на странице
                           )


@routes_bp.route('/applicants/<int:applicant_id>')
def applicant_details(applicant_id):
    applicant = Applicant.query.get_or_404(applicant_id)
    return render_template('applicant_details.html', applicant=applicant)


@routes_bp.route('/contracts/add', methods=['GET', 'POST'])
def add_contract():
    form = AddContractForm()
    organizations = Organization.query.all()
    form.organization_id.choices = [(org.id, org.name) for org in organizations]

    if request.method == 'POST':
        if form.validate_on_submit():
            try:
                new_contract = Contract(
                    number=form.number.data,
                    contract_date=form.contract_date.data,
                    name=form.name.data,
                    expiration_date=form.expiration_date.data,
                    is_extended=form.is_extended.data,
                    organization_id=form.organization_id.data,
                    additional_info=form.additional_info.data
                )
                db.session.add(new_contract)
                db.session.commit()
                flash('Новый контракт успешно добавлен!', 'success')
                return redirect(url_for('routes.contract_details', contract_id=new_contract.id))
            except Exception as e:
                db.session.rollback()
                print(f"Ошибка при добавлении контракта: {e}")
                flash('Произошла ошибка при добавлении контракта. Попробуйте позже.', 'danger')

    return render_template('add_contract.html', form=form, organizations=organizations)


@routes_bp.route('/contracts/<int:contract_id>')
def contract_details(contract_id):
    contract = Contract.query.get_or_404(contract_id)
    return render_template('contract_details.html', contract=contract)
