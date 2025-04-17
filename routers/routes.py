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
                           AttestationType)
from database import db
# from .forms import AddApplicantForm

from werkzeug.security import generate_password_hash
from datetime import datetime

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
            # получаем все поля из формы
            first_name = request.form.get('first_name')
            last_name = request.form.get('last_name')
            middle_name = request.form.get('middle_name')
            username = request.form.get('username')
            email = request.form.get('email')
            password = request.form.get('password')
            phone = request.form.get('phone')
            role_ids = request.form.getlist('role_id')  # получаем список выбранных ролей
            dept_id = request.form.get('dept_id')
            status_id = request.form.get('status_id')

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
            flash('Новый пользователь успешно добавлен!', 'success')  # сообщение об успехе
            return redirect(url_for('routes.user_details', user_id=new_user.id))  # редирект

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
    contingents = Contingent.query.all()
    work_fields = WorkField.query.all()
    applicant_types = ApplicantType.query.all()
    attestation_types = AttestationType.query.all()
    users = User.query.all()  # Загружаем список пользователей для выбора редактора

    if request.method == 'POST':
        try:
            # Получаем данные из формы
            # ... (получение данных из request.form, аналогично add_user) ...
            edited_by_user_id = request.form.get('edited_by_user_id')
            editing_by_id = request.form.get('editing_by_id')  # Поле для выбора текущего редактора

            new_applicant = Applicant(
                # ... (передача данных в конструктор Applicant) ...
                edited_by_user_id=int(edited_by_user_id) if edited_by_user_id else None,
                # Приведение к int, проверка на None
                edited_time=datetime.utcnow(),
                is_editing_now=False,
                editing_by_id=int(editing_by_id) if editing_by_id else None,
                editing_started_at=datetime.utcnow()
            )

            db.session.add(new_applicant)
            db.session.commit()

            flash('Новый заявитель успешно добавлен!', 'success')
            return redirect(url_for('routes.applicant_details', applicant_id=new_applicant.id))  # редирект

        except Exception as e:
            db.session.rollback()
            print(e)
            return jsonify({'error': str(e)}), 500

    return render_template('add_applicant.html',
                           contingents=contingents,
                           work_fields=work_fields,
                           applicant_types=applicant_types,
                           attestation_types=attestation_types,
                           users=users)


@routes_bp.route('/applicants/<int:applicant_id>')
def applicant_details(applicant_id):
    applicant = Applicant.query.get_or_404(applicant_id)
    return render_template('applicant_details.html', applicant=applicant)
