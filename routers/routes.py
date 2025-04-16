from flask import (Blueprint,
                   render_template,
                   jsonify,
                   request,
                   redirect,
                   url_for,
                   flash)
from models.models import User, Role, Department, Status
from database import db
from werkzeug.security import generate_password_hash

routes_bp = Blueprint('routes', __name__)  # Создаем blueprint


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


@routes_bp.route('/users/<int:user_id>')  # новый роут для отображения деталей пользователя
def user_details(user_id):
    user = User.query.get_or_404(user_id)
    return render_template('user_details.html', user=user)
