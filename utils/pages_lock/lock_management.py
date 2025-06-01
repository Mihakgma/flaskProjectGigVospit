from flask import flash

from models.models import get_current_nsk_time, User
from utils.pages_lock.lock_info import LockInfo


def check_if_lock_info(obj):
    if not isinstance(obj, LockInfo):
        raise TypeError("Must be a LockInfo object")


class PageLocker:
    """
    A class to manage the locking of edit DB tables page
    lock_info: class with following structure:
    <blueprint_name>.<function_name>.<edited_table_id>.<user_id>
    __LOCKED_PAGES = {key: lock_info, value: get_current_nsk_time (TS with TZ)}
    """
    __LOCKED_PAGES = {}
    __TIMEOUT_SECONDS = 60 * 1  # 60 *15 - for prod - get from DB table access_setting
    __PAGES_LOCKED_TOTAL = 0
    __PAGES_UNLOCKED_TOTAL = 0

    @staticmethod
    def get_locked_pages():
        return PageLocker.__LOCKED_PAGES

    @staticmethod
    def get_timeout():
        return PageLocker.__TIMEOUT_SECONDS

    @staticmethod
    def get_pages_unlocked_total():
        return PageLocker.__PAGES_UNLOCKED_TOTAL

    @staticmethod
    def get_pages_locked_total():
        return PageLocker.__PAGES_LOCKED_TOTAL

    @staticmethod
    def get_summary():
        locked_pages = PageLocker.get_locked_pages()
        lock_info_objs: [LockInfo] = [obj for obj in locked_pages]
        user_ids_count = {}
        for obj in lock_info_objs:
            current_user_id = obj.user_id
            if current_user_id not in user_ids_count:
                user_ids_count[current_user_id] = 1
            else:
                user_ids_count[obj.user_id] = +1
        most_frequent = sorted(user_ids_count.items(), key=lambda x: x[1], reverse=True)
        most_frequent_user_id = most_frequent[0]
        less_frequent = sorted(user_ids_count.items(), key=lambda x: x[1], reverse=False)
        pages_locked_total = PageLocker.get_pages_locked_total()
        pages_unlocked_total = PageLocker.get_pages_unlocked_total()

        out = (f"Всего ЗАблокировано страниц НА ТЕКУЩИЙ МОМЕНТ: <{len(locked_pages)}>, "
               f"Наибольшее число страниц, заблокированных на текущий момент пользователем (id): "
               f"<{most_frequent_user_id}>: <{most_frequent[1]}>, "
               f"Наименьшее число страниц, заблокированных на текущий момент пользователем (id): "
               f"<{less_frequent[0]}>: <{less_frequent[1]}>, "
               f"Всего ЗАблокировано страниц ПОСЛЕ РЕСТАРТА ПРИЛОЖЕНИЯ: <{pages_locked_total}>, "
               f"Всего РАЗблокировано страниц ПОСЛЕ РЕСТАРТА ПРИЛОЖЕНИЯ: <{pages_unlocked_total}>, ")
        return out

    @staticmethod
    def clear_locked_pages():
        PageLocker.__LOCKED_PAGES = {}

    @staticmethod
    def lock_page(lock_data: LockInfo) -> bool:
        check_if_lock_info(lock_data)
        locked_pages = PageLocker.get_locked_pages()
        # ПЕРЕДЕЛАТЬ !!! НЕПРАВИЛЬНО!!!
        # перезаход на редактирование (обновил страницу) одним и тем же пользователем,
        # обновляется таймаут на доступ к странице для пользователя...
        if lock_data in locked_pages:
            locked_pages[lock_data] = get_current_nsk_time()
            flash('Таймаут для текущей страницы - обновлен.', 'warning')
            return True
        # текущая функция и строка в таблице не редактируется пользователем,
        # который пытается зайти в нее на редактирование
        else:
            for locked_page in locked_pages:
                if locked_page.funct_tablerow_equivalence(lock_data):
                    # ДОБАВИТЬ ПРОВЕРКУ НА ТАЙМАУТ РЕДАКТИРОВАНИЯ!!! по истекшему для редактора времени!!!
                    user_id = locked_page.user_id
                    user_editor = User.query.get_or_404(user_id)
                    flash(f'Текущая страница редактируется пользователем: <{user_editor.full_name}>',
                          'danger')
                    return False
        locked_pages[lock_data] = get_current_nsk_time()
        return True

    @staticmethod
    def unlock_page(lock_data: LockInfo):
        check_if_lock_info(lock_data)
        locked_pages = PageLocker.get_locked_pages()
        locked_pages.pop(lock_data, None)
