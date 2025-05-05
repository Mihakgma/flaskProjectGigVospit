from flask import (Blueprint,
                   render_template,
                   redirect,
                   url_for,
                   flash)
from flask_login import login_required

from functions.access_control import role_required
from models.models import (User,
                           Role)
from database import db

from werkzeug.security import generate_password_hash
from sqlalchemy.exc import IntegrityError

from forms.forms import UserAddForm

users_bp = Blueprint('users', __name__)


@users_bp.route('/users')
@login_required
def users():
    users = User.query.all()
    return render_template('list.html', users=users)


@users_bp.route('/add', methods=['GET', 'POST'])
# @role_required('admin', )
def add_user():
    form = UserAddForm()
    # form.populate_role_choices()

    if form.validate_on_submit():
        try:
            existing_user = User.query.filter_by(username=form.username.data).first()
            if existing_user:
                flash('Имя пользователя уже существует.', 'danger')
                return render_template('add_user.html', form=form)

            hashed_password = generate_password_hash(form.password.data, method='pbkdf2:sha256')

            role_objects = []
            for role_id in form.roles.data:
                role = Role.query.get(role_id)
                if role is not None:
                    role_objects.append(role)

            new_user = User(
                first_name=form.first_name.data,
                last_name=form.last_name.data,
                middle_name=form.middle_name.data,
                username=form.username.data,
                email=form.email.data,
                password=hashed_password,
                phone=form.phone.data,
                dept_id=form.dept_id.data.id,
                status_id=form.status_id.data.id,
                info=form.info.data,
                roles=role_objects
            )

            db.session.add(new_user)
            db.session.commit()

            flash('Новый пользователь успешно добавлен!', 'success')
            return redirect(url_for('users.user_details', user_id=new_user.id))

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
            return render_template('add_user.html',
                                   form=form)

        except Exception as e:
            db.session.rollback()
            flash(f'Произошла непредвиденная ошибка: {str(e)}', 'danger')
            return render_template('add_user.html',
                                   form=form)

    return render_template('add_user.html',
                           form=form)


@users_bp.route('/details/<int:user_id>/',
                methods=['GET'])
@login_required
@role_required('admin', 'moder', 'oper', )
def user_details(user_id):
    user = User.query.get_or_404(user_id)
    return render_template('user_details.html', user=user)
