from flask import flash

from models.models import get_current_nsk_time, User, AccessSetting
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
    __TIMEOUT_SECONDS = 60  # 60 * 15 - for prod - get from DB table access_setting
    __PAGES_LOCKED_TOTAL = 0
    __PAGES_UNLOCKED_TOTAL = 0
    # кратность количества заблокированных страниц, при которой происходит очистка основного контейнера класса
    __PERIOD_CONTAINER_CLEAN = 30

    @staticmethod
    def pages_lock_increment():
        PageLocker.__PAGES_LOCKED_TOTAL += 1

    @staticmethod
    def pages_unlock_increment():
        PageLocker.__PAGES_UNLOCKED_TOTAL += 1

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

        most_frequent_user_id, most_frequent_pages_num = 0, 0
        less_frequent_user_id, less_frequent_pages_num = 0, 0

        try:
            most_frequent = sorted(user_ids_count.items(), key=lambda x: x[1], reverse=True)
            most_frequent_user_id, most_frequent_pages_num = most_frequent[0], most_frequent[1]
            less_frequent = sorted(user_ids_count.items(), key=lambda x: x[1], reverse=False)
            less_frequent_user_id, less_frequent_pages_num = less_frequent[0], less_frequent[1]
        except IndexError as e:
            print(str(e))

        pages_locked_total = PageLocker.get_pages_locked_total()
        pages_unlocked_total = PageLocker.get_pages_unlocked_total()

        out = (f"Всего Заблокировано страниц НА ТЕКУЩИЙ МОМЕНТ: <{len(locked_pages)}>, "
               f"Наибольшее число страниц, заблокированных на текущий момент пользователем (id): "
               f"<{most_frequent_user_id}>: <{most_frequent_pages_num}>, "
               f"Наименьшее число страниц, заблокированных на текущий момент пользователем (id): "
               f"<{less_frequent_user_id}>: <{less_frequent_pages_num}>, "
               f"Всего Заблокировано страниц ПОСЛЕ РАЗБЛОКИРОВАНИЯ ВСЕХ СТРАНИЦ: <{pages_locked_total}>, "
               f"Разблокировано страниц (по времени простоя) ПОСЛЕ РАЗБЛОКИРОВАНИЯ ВСЕХ СТРАНИЦ: "
               f"<{pages_unlocked_total}>.")
        return out

    @staticmethod
    def clear_all_lock_info():
        PageLocker.__LOCKED_PAGES = {}
        PageLocker.__PAGES_LOCKED_TOTAL = 0
        PageLocker.__PAGES_UNLOCKED_TOTAL = 0
        activated_setting = AccessSetting.get_activated_setting()
        activated_setting_name = activated_setting.name
        PageLocker.__TIMEOUT_SECONDS = activated_setting.page_lock_seconds
        print(f"Параметр __TIMEOUT_SECONDS установлен из сеттинга: <{activated_setting_name}>: "
              f"<{activated_setting.page_lock_seconds}>")

    @staticmethod
    def lock_page(lock_data: LockInfo) -> bool:
        check_if_lock_info(lock_data)
        locked_pages = PageLocker.get_locked_pages()
        timeout = PageLocker.get_timeout()
        lock_counter = PageLocker.get_pages_locked_total()
        container_clean_period = PageLocker.__PERIOD_CONTAINER_CLEAN
        if lock_counter and lock_counter % container_clean_period == 0:
            pages_to_purge = []
            now_ts = get_current_nsk_time()
            for locked_page in locked_pages:
                lock_time = locked_pages[locked_page]
                secs_elapsed = (now_ts - lock_time).seconds
                is_time_out = secs_elapsed > timeout
                if is_time_out:
                    pages_to_purge.append(locked_page)
            [PageLocker.unlock_page(page) for page in pages_to_purge]
            flash(f'Контейнер класса PageLocker очищен на <{len(pages_to_purge)}> элементов.',
                  'success')
        # перезаход на редактирование (обновил страницу) одним и тем же пользователем,
        # обновляется таймаут на доступ к странице для пользователя...
        if lock_data in locked_pages:
            locked_pages[lock_data] = get_current_nsk_time()
            flash('Таймаут для текущей страницы - обновлен.', 'warning')
            PageLocker.pages_lock_increment()
            return True
        # текущая функция и строка в таблице не редактируется пользователем,
        # который пытается зайти в нее на редактирование
        else:
            for locked_page in locked_pages:
                last_activity_at = locked_pages[locked_page]
                secs_elapsed = (get_current_nsk_time() - last_activity_at).seconds
                is_time_out = secs_elapsed > timeout
                if locked_page.funct_tablerow_equivalence(lock_data) and not is_time_out:
                    # ДОБАВИТЬ ПРОВЕРКУ НА ТАЙМАУТ РЕДАКТИРОВАНИЯ!!! по истекшему для редактора времени!!!
                    user_id = locked_page.user_id
                    user_editor = User.query.get_or_404(user_id)
                    flash(f'Текущая страница редактируется пользователем: <{user_editor.full_name}>,'
                          f'Время до авто-разблокировки страницы: <{timeout - secs_elapsed}> сек.',
                          'danger')
                    return False
                elif locked_page.funct_tablerow_equivalence(lock_data) and is_time_out:
                    user_id = locked_page.user_id
                    user_editor = User.query.get_or_404(user_id)
                    flash(f'У пользователем: <{user_editor.full_name}> вышло '
                          f'максимально возможное время на редактирование страницы ({timeout}) сек.',
                          'warning')
                    PageLocker.unlock_page(locked_page)
                    locked_pages[lock_data] = get_current_nsk_time()
                    PageLocker.pages_lock_increment()
                    PageLocker.pages_unlock_increment()
                    return True
        locked_pages[lock_data] = get_current_nsk_time()
        PageLocker.pages_lock_increment()
        return True

    @staticmethod
    def unlock_page(lock_data: LockInfo):
        check_if_lock_info(lock_data)
        locked_pages = PageLocker.get_locked_pages()
        locked_pages.pop(lock_data, None)

    @staticmethod
    def unlock_all_user_pages(user_id: int):
        locked_pages = PageLocker.get_locked_pages()
        locked_pages = list(locked_pages)
        counter = 0

        # Получаем объект пользователя по user_id, переданному в функцию
        # Делаем это ДО цикла, так как flash-сообщение оперирует общим user_id функции.
        user_to_unlock = User.query.get(user_id)

        # Определяем отображаемое имя пользователя
        if user_to_unlock:
            username_display = user_to_unlock.username
        else:
            username_display = f"ID {user_id} (пользователь не найден)"

        for locked_page in locked_pages:
            lock_user_id = locked_page.get_user_id()
            if user_id == lock_user_id:  # Проверка, что user_id совпадает с user_id, который заблокировал страницу
                counter += 1
                PageLocker.unlock_page(locked_page)

        # Выводим flash-сообщение
        flash(f'Разблокировано <{counter}> страниц, '
              f'заблокированных пользователем: <{username_display}>')
