from flask import flash, redirect, url_for

from database import db
from functions import get_ip_address
from models import User
from models.models import get_current_nsk_time
from sqlalchemy.exc import IntegrityError


class UserCrudControl:
    """
    Сущность БД может как передаваться прямо при создании объекта текущего класса,
    так и не передаваться, т.е. использоваться напрямую из своего модуля
    if need_commit == False, тогда
    коммит внесенных изменений в сессию происходит снаружи,
    т.е. не внутри методов класса!
    :return:
    """
    __ACTIVITY_TIMEOUT_SECONDS = 60  # 15 min = 900 secs, test = 60-120-180 secs
    __USERS_LAST_ACTIVITY = {}
    __ACTIVITY_COUNTER = 0
    __ACTIVITY_COUNTER_MAX_THRESHOLD = 10  # 10000 optimal
    __ACTIVITY_PERIOD_COUNTER = 5  # 50 and >
    __USERS_OBJECTS = []

    def __init__(self,
                 user: User,
                 need_commit: bool = True,
                 db_object: db = db):
        self.__need_commit = need_commit
        self.__db_object = db_object
        self.__user = user

    def get_user(self):
        return self.__user

    def get_db_object(self):
        return self.__db_object

    def get_need_commit(self):
        return self.__need_commit

    @staticmethod
    def get_activity_counter():
        return UserCrudControl.__ACTIVITY_COUNTER

    @staticmethod
    def increment_counter():
        UserCrudControl.__ACTIVITY_COUNTER += 1

    @staticmethod
    def clear_counter():
        UserCrudControl.__ACTIVITY_COUNTER = 0

    @staticmethod
    def get_timeout():
        return UserCrudControl.__ACTIVITY_TIMEOUT_SECONDS

    @staticmethod
    def update_users_last_activity(user_id: int):
        UserCrudControl.increment_counter()
        UserCrudControl.__USERS_LAST_ACTIVITY[user_id] = get_current_nsk_time()

    @staticmethod
    def reset_users_last_activity():
        UserCrudControl.clear_counter()
        UserCrudControl.__USERS_LAST_ACTIVITY = {}

    @staticmethod
    def clear_users_last_activity(user_id: int):
        UserCrudControl.__USERS_LAST_ACTIVITY[user_id] = ""

    @staticmethod
    def get_activity_period_counter():
        return UserCrudControl.__ACTIVITY_PERIOD_COUNTER

    @staticmethod
    def update_users():
        UserCrudControl.__USERS_OBJECTS = User.query.all()

    @staticmethod
    def get_users():
        return UserCrudControl.__USERS_OBJECTS

    @staticmethod
    def get_users_last_activity():
        return UserCrudControl.__USERS_LAST_ACTIVITY

    @staticmethod
    def get_activity_counter_max_threshold():
        return UserCrudControl.__ACTIVITY_COUNTER_MAX_THRESHOLD

    def login(self):
        """
        ЗДЕСЬ РЕАЛИЗОВАНА ЗАЩИТА ОТ ЕДИНОВРЕМЕННОГО ВХОДА С РАЗНЫМ ПК (РАБОЧИХ МАШИН)
        ДЛЯ ВСЕХ ПОЛЬЗОВАТЕЛЕЙ ЗА ИСКЛЮЧЕНИЕМ АДМИНИСТРАТОРА (-ОВ) ПРИЛОЖЕНИЯ
        :return:
        """
        db_obj = self.get_db_object()
        user = self.get_user()
        need_commit = self.get_need_commit()
        roles = user.roles
        user_roles = {role.code for role in roles}
        users = User.query.all()
        ip_addresses = [user.valid_ip for user in users]
        client_ip_address = get_ip_address()
        user_ip_address = User.query.filter_by(valid_ip=client_ip_address).first()
        try:
            user.is_logged_in = True
            user.logged_in_at = get_current_nsk_time()
            if "admin" in user_roles:
                user.valid_ip = client_ip_address
            elif client_ip_address in ip_addresses and user.id != user_ip_address.id:
                flash(f'Cannot log in as {user.username}. You are already logged in as <{user_ip_address.username}>',
                      'danger')
                return False
            elif not user.valid_ip or user.valid_ip == "":
                user.valid_ip = client_ip_address
            elif user.valid_ip != client_ip_address:
                flash(
                    f'Username <{user.username}> has already been logged in through IP-address: <{client_ip_address}>',
                    'danger')
                return False
            user.last_activity_at = get_current_nsk_time()
            db_obj.session.add(user)
            if need_commit:
                db_obj.session.commit()
                flash('Users лог-данные успешно обновлены!', 'success')
            return True
        except IntegrityError as ie:
            db_obj.session.rollback()
            flash(f'Error: <{ie}>', 'danger')
            return False
        except Exception as e:
            db_obj.session.rollback()
            flash(f'Произошла неожиданная ошибка: {e} при попытке залогиниться пользователю:'
                  f' <{user.username}>',
                  'danger')
            return False

    def logout(self):
        db_obj = self.get_db_object()
        user = self.get_user()
        need_commit = self.get_need_commit()
        try:
            user.is_logged_in = False
            user.valid_ip = ""
            user.last_activity_at = get_current_nsk_time()
            db_obj.session.add(user)
            UserCrudControl.clear_users_last_activity(user_id=user.id)
            if need_commit:
                db_obj.session.commit()
            flash('Users лог-данные успешно обновлены!', 'success')
            return redirect(url_for('auth.login'))
        except IntegrityError as ie:
            db_obj.session.rollback()
            flash(f'Error: <{ie}>', 'danger')
        except Exception as e:
            db_obj.session.rollback()
            flash(f'Произошла неожиданная ошибка: {e} при попытке выйти из приложения пользователю:'
                  f' <{user.username}>',
                  'danger')

    def commit_other_table(self):
        """
        Юзер совершает успешный коммит в любую таблицу БД
        :return:
        """
        db_obj = self.get_db_object()
        user = self.get_user()
        user.last_commit_at = get_current_nsk_time()
        db_obj.session.add(user)

    @staticmethod
    def sessions_restart(db_obj,
                         users: list,
                         need_commit: bool):
        """
        Применяется при рестарте приложения:
        обнуляем всем юзерам IP-адреса, юзеры зареганы - фолс
        :return:
        """
        UserCrudControl.reset_users_last_activity()
        for user in users:
            try:
                user.is_logged_in = False
                user.valid_ip = ""
                user.last_activity_at = get_current_nsk_time()
                db_obj.session.add(user)
                if need_commit:
                    db_obj.session.commit()
            except IntegrityError as ie:
                db_obj.session.rollback()  # Откатываем изменения
                print(f'Error: <{ie}>', 'danger')
            except Exception as e:  # Ловим любые другие неожиданные ошибки
                db_obj.session.rollback()
                print(f'Произошла неожиданная ошибка: {e} при обнулении дефолтными значениями для пользователя:'
                      f' <{user.username}>', 'danger')

    @staticmethod
    def check_all_users_last_activity(current_user):

        counter = UserCrudControl.get_activity_counter()
        period = UserCrudControl.get_activity_period_counter()
        max_counter = UserCrudControl.get_activity_counter_max_threshold()
        # debugging flash
        flash(f'COUNTER = <{counter}>,'
              f' period = <{period}>, '
              f'max_counter = <{max_counter}>', 'warning')
        if counter and (counter % period == 0) and counter < max_counter:
            UserCrudControl.update_users_last_activity(user_id=current_user.id)
            timeout = UserCrudControl.get_timeout()
            UserCrudControl.update_users()
            users = UserCrudControl.get_users()
            users_last_activity = UserCrudControl.get_users_last_activity()
            # debugging flash
            flash(f'<{[(k,v) for (k,v) in users_last_activity.items()]}>', 'warning')

            for user_to_check in users:
                if (user_to_check.is_logged_in
                        and user_to_check.id != current_user.id
                        and users_last_activity[user_to_check.id] != ""):
                    last_activity_at = users_last_activity[user_to_check.id]
                    is_time_out = (get_current_nsk_time() - last_activity_at).seconds > timeout
                    if is_time_out:
                        flash(
                            f"Пользователь {user_to_check.username} вышел из системы по таймауту ({timeout} сек).",
                            "warning")
                        user_ctrl_obj = UserCrudControl(user=user_to_check)
                        # debugging flash
                        # flash(f'<[{[(k,v) for (k,v) in user_ctrl_obj.__dict__.items()]}]>', 'danger')
                        user_ctrl_obj.logout()  # Метод logout() сам позаботится о коммите.
                elif (not user_to_check.is_logged_in
                      and user_to_check.id != current_user.id
                      and user_to_check.id in users_last_activity
                      and users_last_activity[user_to_check.id] is not None):
                    last_activity_at = users_last_activity[user_to_check.id]
                    if last_activity_at == "":
                        pass
                    else:
                        is_time_out = (get_current_nsk_time() - last_activity_at).seconds > timeout
                        if is_time_out:
                            flash(
                                f"Пользователь {user_to_check.username} вышел из системы по таймауту ({timeout} сек).",
                                "warning")
                            user_ctrl_obj = UserCrudControl(user=user_to_check)
                            # debugging flash
                            # flash(f'<[{[(k,v) for (k,v) in user_ctrl_obj.__dict__.items()]}]>', 'danger')
                            user_ctrl_obj.logout()  # Метод logout() сам позаботится о коммите.
        elif counter >= max_counter:
            # flash & restart all sessions!
            flash(f'Достигнут предел обращений к программе в рамках одного запуска: <{max_counter}>'
                  f'Для продолжения работы потребуется повторная авторизация!',
                  'warning')
            UserCrudControl.update_users()
            users = UserCrudControl.get_users()
            UserCrudControl.sessions_restart(db_obj=db, users=users, need_commit=True)
        else:
            UserCrudControl.update_users_last_activity(user_id=current_user.id)
