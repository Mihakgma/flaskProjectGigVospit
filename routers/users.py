from flask import (Blueprint,
                   render_template,
                   redirect,
                   url_for,
                   flash, request, current_app)
from flask_login import login_required

from functions.access_control import role_required
from models.models import (User,
                           Role)
from database import db

from werkzeug.security import generate_password_hash
from sqlalchemy.exc import IntegrityError

from forms.forms import UserForm

users_bp = Blueprint('users', __name__)


@users_bp.route('/users')
@login_required
@role_required('admin', 'moder', )
def user_list():
    users_lst = User.query.all()
    return render_template('user_list.html', users=users_lst)


@users_bp.route('/add', methods=['GET', 'POST'])
@login_required
@role_required('admin')
def add_user():
    form = UserForm()
    if form.validate_on_submit():
        try:
            # Валидаторы формы уже проверят уникальность username и email
            hashed_password = generate_password_hash(form.password.data, method='pbkdf2:sha256') \
                if form.password.data else None  # Пароль обязателен при добавлении

            if not hashed_password:  # Дополнительная проверка, что пароль введен при добавлении
                flash('Пароль обязателен при создании нового пользователя.', 'danger')
                return render_template('user_form.html', form=form, title='Добавление нового пользователя',
                                       submit_button_text='Добавить')

            selected_roles = Role.query.filter(Role.id.in_(form.roles.data)).all()

            new_user = User(
                first_name=form.first_name.data,
                last_name=form.last_name.data,
                middle_name=form.middle_name.data if form.middle_name.data else None,
                username=form.username.data,
                email=form.email.data,
                password=hashed_password,
                phone=form.phone.data if form.phone.data else None,
                department=form.dept_id.data,  # QuerySelectField возвращает объект модели
                status=form.status_id.data,  # QuerySelectField возвращает объект модели
                info=form.info.data if form.info.data else None,
                roles=selected_roles
            )
            db.session.add(new_user)
            db.session.commit()
            flash('Новый пользователь успешно добавлен!', 'success')
            return redirect(url_for('users_bp.user_details', user_id=new_user.id))
        except IntegrityError as e:
            db.session.rollback()
            current_app.logger.error(f"IntegrityError on user add: {e}")
            flash('Ошибка базы данных. Возможно, такое имя пользователя или email уже существует.', 'danger')
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Exception on user add: {e}")
            flash(f'Произошла непредвиденная ошибка: {str(e)}', 'danger')

    return render_template('user_form.html', form=form, title='Добавление нового пользователя',
                           submit_button_text='Добавить')


@users_bp.route('/edit/<int:user_id>', methods=['GET', 'POST'])
@login_required
@role_required('admin', 'moder')  # Укажите нужные роли
def edit_user(user_id):
    user_to_edit = User.query.get_or_404(user_id)
    # Передаем original_username и original_email для валидаторов
    form = UserForm(obj=user_to_edit, original_username=user_to_edit.username, original_email=user_to_edit.email)

    if form.validate_on_submit():
        try:
            user_to_edit.first_name = form.first_name.data
            user_to_edit.last_name = form.last_name.data
            user_to_edit.middle_name = form.middle_name.data if form.middle_name.data else None
            user_to_edit.username = form.username.data
            user_to_edit.email = form.email.data
            user_to_edit.phone = form.phone.data if form.phone.data else None
            user_to_edit.department = form.dept_id.data  # QuerySelectField возвращает объект
            user_to_edit.status = form.status_id.data  # QuerySelectField возвращает объект
            user_to_edit.info = form.info.data if form.info.data else None

            if form.password.data:  # Обновляем пароль, только если он введен
                user_to_edit.password = generate_password_hash(form.password.data, method='pbkdf2:sha256')

            selected_roles = Role.query.filter(Role.id.in_(form.roles.data)).all()
            user_to_edit.roles = selected_roles

            db.session.commit()
            flash('Данные пользователя успешно обновлены!', 'success')
            return redirect(url_for('users_bp.user_details', user_id=user_to_edit.id))
        except IntegrityError as e:
            db.session.rollback()
            current_app.logger.error(f"IntegrityError on user edit: {e}")
            flash('Ошибка базы данных. Возможно, такое имя пользователя или email уже занято другим пользователем.',
                  'danger')
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Exception on user edit: {e}")
            flash(f'Произошла непредвиденная ошибка при обновлении: {str(e)}', 'danger')
    elif request.method == 'POST':  # Если POST и форма невалидна
        flash('Пожалуйста, исправьте ошибки в форме.', 'warning')

    # Для GET-запроса или если POST-запрос не прошел валидацию,
    # форма должна быть предзаполнена данными (obj=user_to_edit это делает).
    # Явно устанавливаем data для полей, где obj может не сработать идеально,
    # или для обеспечения консистентности.
    if request.method == 'GET':
        form.first_name.data = user_to_edit.first_name
        form.last_name.data = user_to_edit.last_name
        form.middle_name.data = user_to_edit.middle_name
        form.username.data = user_to_edit.username
        form.email.data = user_to_edit.email
        form.phone.data = user_to_edit.phone
        form.dept_id.data = user_to_edit.department
        form.status_id.data = user_to_edit.status
        form.info.data = user_to_edit.info
        form.roles.data = [role.id for role in user_to_edit.roles]  # Для SelectMultipleField нужны ID

    return render_template('user_form.html',
                           form=form,
                           title=f'Редактирование пользователя: {user_to_edit.username}',
                           submit_button_text='Сохранить изменения',
                           user=user_to_edit)  # Передаем пользователя для контекста в шаблоне


@users_bp.route('/details/<int:user_id>/',
                methods=['GET'])
@login_required
@role_required('admin', 'moder', 'oper', )
def user_details(user_id):
    user = User.query.get_or_404(user_id)
    return render_template('user_details.html', user=user)
