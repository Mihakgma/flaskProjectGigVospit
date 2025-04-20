from flask import (Blueprint,
                   render_template,
                   jsonify,
                   request,
                   redirect,
                   url_for,
                   flash, session)

from functions.access_control import role_required
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

from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timezone
from sqlalchemy.exc import IntegrityError

from routers.forms import (AddApplicantForm,
                           AddContractForm,
                           LoginForm,
                           RegistrationForm,
                           UserAddForm)

from flask_login import (login_user,
                         logout_user,
                         current_user,
                         login_required)

routes_bp = Blueprint('routes', __name__)  # Создаем blueprint
auth_bp = Blueprint('auth', __name__)  # Создаем blueprint
logout_bp = Blueprint('logout', __name__)  # Создаем blueprint

# Словарь с описанием роутов
ROUTES_INFO = [
    {'path': '/users/add', 'title': 'Форма для добавления пользователя с ролями, отделом и статусом.'},
    {'path': '/users/<int:user_id>', 'title': 'Отображает детали пользователя.'},
    {'path': '/applicants/add', 'title': 'Добавить нового заявителя'},
    {'path': '/applicants/<int:applicant_id>', 'title': 'Отображает детали заявителя'},
    {'path': '/auth/register', 'title': 'Регистрация нового пользователя', 'route': 'auth.register'},
    {'path': '/auth/login', 'title': 'Войти в систему', 'route': 'auth.login'}
]


@auth_bp.route('/register', methods=['GET', 'POST'])
@role_required('admin')
def register():
    if current_user.is_authenticated:
        return redirect(url_for('routes.index'))  # Или другой роут главной страницы

    form = RegistrationForm()
    form.populate_role_choices()  # Здесь заполняются варианты выбора ролей

    if form.validate_on_submit():
        hashed_password = generate_password_hash(form.password.data, method='pbkdf2:sha256')
        user = User(last_name=form.last_name.data,
                    first_name=form.first_name.data,
                    username=form.username.data,
                    email=form.email.data,
                    password=hashed_password,
                    roles=[Role.query.get(form.role.data)])
        db.session.add(user)
        db.session.commit()
        flash('Вы успешно зарегистрировались! Теперь вы можете войти.', 'success')
        return redirect(url_for('auth.login'))  # Перенаправляем на страницу входа

    return render_template('register.html', title='Регистрация', form=form)


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        username = form.username.data
        password = form.password.data
        remember_me = form.remember_me.data

        user = User.query.filter_by(username=username).first()
        if user is None or not check_password_hash(user.password, password):
            flash('Неверный логин или пароль.')
            return render_template('login.html', title='Авторизация', form=form)

        session['user'] = {
            'id': user.id,
            'username': user.username,
            'roles': [role.code for role in user.roles]
        }
        login_user(user, remember=remember_me)
        next_page = request.args.get('next')
        return redirect(next_page or url_for('routes.index'))
    return render_template('login.html', title='Авторизация', form=form)


@logout_bp.route('/logout')
@login_required  # Защищаем роут logout
def logout():
    logout_user()
    return redirect(url_for('routes.index'))  # Или другой роут главной страницы


@routes_bp.route('/')
def index():
    return render_template('index.html', routes=ROUTES_INFO)


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
@role_required(['admin'])
def add_user():
    form = UserAddForm()
    form.dept_id.choices = [(d.id, d.name) for d in Department.query.all()]
    form.status_id.choices = [(s.id, s.name) for s in Status.query.all()]
    form.role_ids.choices = [(r.id, r.name) for r in Role.query.all()]

    if form.validate_on_submit():
        try:
            existing_user = User.query.filter_by(username=form.username.data).first()
            if existing_user:
                flash('Имя пользователя уже существует.', 'danger')
                return render_template('add_user.html', form=form)

            hashed_password = generate_password_hash(form.password.data, method='pbkdf2:sha256')

            new_user = User(
                first_name=form.first_name.data,
                last_name=form.last_name.data,
                middle_name=form.middle_name.data,
                username=form.username.data,
                email=form.email.data,
                password=hashed_password,
                phone=form.phone.data,
                dept_id=form.dept_id.data,
                status_id=form.status_id.data,
                user_code=form.user_code.data  # Не забудьте про user_code!
            )

            selected_roles = Role.query.filter(Role.id.in_(form.role_ids.data)).all()
            new_user.roles.extend(selected_roles)

            db.session.add(new_user)
            db.session.commit()

            flash('Новый пользователь успешно добавлен!', 'success')
            return redirect(url_for('routes.user_details', user_id=new_user.id))

        except IntegrityError as e:
            db.session.rollback()
            if 'UNIQUE constraint failed' in str(e):
                if 'username' in str(e):
                    flash('Пользователь с таким именем пользователя уже существует.', 'danger')
                elif 'email' in str(e):
                    flash('Пользователь с таким email уже существует.', 'danger')
                elif 'user_code' in str(e):  # Проверяем на уникальность user_code
                    flash('Пользователь с таким кодом пользователя уже существует.', 'danger')
                else:  # обрабатываем все остальные UNIQUE constraint failed ошибки
                    flash(f'Ошибка базы данных: {e.orig.msg}', 'danger')
            else:
                flash(f'Ошибка базы данных: {e.orig.msg}', 'danger')
            return render_template('add_user.html', form=form)

        except Exception as e:
            db.session.rollback()
            flash(f'Произошла непредвиденная ошибка: {str(e)}', 'danger')
            return render_template('add_user.html', form=form)

    return render_template('add_user.html', form=form)


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
    return render_template('applicant_details.html',
                           applicant=applicant,
                           timezone=timezone)


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
