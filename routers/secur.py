from flask import (Blueprint,
                   render_template,
                   request,
                   redirect,
                   url_for,
                   flash, session)

from models.models import User

from werkzeug.security import check_password_hash

from forms.forms import (LoginForm)

from flask_login import (login_user,
                         logout_user,
                         current_user)

from utils.crud_classes import UserCrudControl

auth_bp = Blueprint('auth', __name__)


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
        # ЗДЕСЬ БУДЕТ КРУД ДЛЯ ЛОГИРОВАНИЯ ВХОДА ЮЗЕРОВ!!!
        user_crud_control = UserCrudControl(user=user,
                                            need_commit=True)
        if not user_crud_control.login():
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
# @login_required
def logout():
    form = LoginForm()
    user = current_user
    user_crud_control = UserCrudControl(user=user,
                                        need_commit=True)
    user_crud_control.logout()
    logout_user()
    return redirect(url_for('auth.login'))
