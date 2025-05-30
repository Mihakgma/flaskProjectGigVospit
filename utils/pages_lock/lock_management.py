from models.models import get_current_nsk_time
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
    __TIMEOUT_SECONDS = 60 * 15
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
        lock_info_objs = [obj for obj in locked_pages]
        pages_locked_total = PageLocker.get_pages_locked_total()
        pages_unlocked_total = PageLocker.get_pages_unlocked_total()

        out = (f"Всего ЗАблокировано страниц НА ТЕКУЩИЙ МОМЕНТ: <{len(locked_pages)}>, "
               f"Всего ЗАблокировано страниц ПОСЛЕ РЕСТАРТА ПРИЛОЖЕНИЯ: <{pages_locked_total}>, "
               f"Всего РАЗблокировано страниц ПОСЛЕ РЕСТАРТА ПРИЛОЖЕНИЯ: <{pages_unlocked_total}>, ")
        return out

    @staticmethod
    def clear_locked_pages():
        PageLocker.__LOCKED_PAGES = {}

    @staticmethod
    def lock_page(lock_info: LockInfo):
        check_if_lock_info(lock_info)
        locked_pages = PageLocker.get_locked_pages()
        if lock_info not in locked_pages:
            locked_pages[lock_info] = get_current_nsk_time()

    @staticmethod
    def unlock_page(lock_info: LockInfo):
        check_if_lock_info(lock_info)
        locked_pages = PageLocker.get_locked_pages()
        locked_pages.pop(lock_info, None)
