from flask import (Blueprint,
                   render_template,
                   request,
                   redirect,
                   url_for,
                   flash, session)

from models.models import (User,
                           Role)

from database import db

from werkzeug.security import generate_password_hash, check_password_hash

from forms.forms import (LoginForm,
                         RegistrationForm)
import logging

from flask_login import (login_user,
                         logout_user,
                         current_user)

auth_bp = Blueprint('auth', __name__)  # Создаем blueprint


@auth_bp.route('/register', methods=['GET', 'POST'])
# @role_required('admin')
def register():
    if current_user.is_authenticated:
        return redirect(url_for('routes.index'))

    form = RegistrationForm()
    form.populate_role_choices()  # Загружаем роли для выбора

    if form.validate_on_submit():
        hashed_password = generate_password_hash(form.password.data, method='pbkdf2:sha256')

        # Создаем новый экземпляр пользователя
        new_user = User(
            last_name=form.last_name.data,
            first_name=form.first_name.data,
            username=form.username.data,
            email=form.email.data,
            password=hashed_password
        )

        # Присваиваем выбранные роли
        new_user.roles.extend(Role.query.filter(Role.id.in_(form.roles.data)).all())

        try:
            db.session.add(new_user)
            db.session.commit()
            flash('Вы успешно зарегистрировались!', category='success')
            return redirect(url_for('auth.login'))
        except Exception as e:
            db.session.rollback()
            flash('Возникла ошибка при регистрации. Попробуйте снова позже.', category='danger')
            logging.error(str(e))  # Логирование исключения

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


@auth_bp.route('/logout')
# @login_required  # Защищаем роут logout
def logout():
    form = LoginForm()
    logout_user()
    return render_template('login.html',
                           title='Авторизация',
                           form=form)
