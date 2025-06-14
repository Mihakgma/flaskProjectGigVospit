from functools import wraps
from threading import Thread, Event
from threading import enumerate as thread_enumerate
from time import sleep as time_sleep

from flask import request, current_app, flash, redirect, url_for


def thread(func):
    """
    Это простейший декоратор. В него мы будем заворачивать
    функции. Любая функция, завернутая этим декоратором,
    будет выполнена в отдельном потоке.
    :param func:
    :return:
    """

    @wraps(func)
    def wrapper(*args, **kwargs):
        with current_app.app_context():
            current_thread = Thread(
                target=func,
                args=args,
                kwargs=kwargs,
                name=func.__name__,
                daemon=True)
            current_thread.start()
            return func(*args, **kwargs)

    return wrapper


def background_task(f, redirect_to='applicants.search_applicants'):
    @wraps(f)
    def wrapped(*args, **kwargs):
        # Получаем данные из request context ДО его закрытия
        # applicant_ids_str = request.form.get('applicant_ids')

        # Получаем текущее приложение для восстановления контекста
        app_context = current_app._get_current_object()

        # Создаем новый поток
        t = Thread(target=f, args=(app_context, *args),
                   kwargs=kwargs)  # Передаем applicant_ids_str и app_context
        t.daemon = True  # Или False, если хотите, чтобы задача завершилась, даже если главный процесс умрет
        t.start()
        # Возвращаем ответ сразу, не дожидаясь завершения потока
        flash('Экспорт данных запущен в фоновом режиме. Файл будет создан.', 'info')
        return redirect(url_for(redirect_to))  # или куда-то еще

    return wrapped


def stop_thread(thread_name: str):
    print(thread_name)
    for t in thread_enumerate():
        print(t.name)
        try:
            if t.name == thread_name:
                print(f"<{t}> has been detected...")
                if t.is_alive():
                    t.__setattr__("is_alive", False)
                    t._stop_event = Event()
                    t._stop_event.set()
                    print(f" - {t.name} ({t.ident}) has successfully stopped")
        except Exception as e:
            print(f" Error getting info of: {t.name}: {e}")


@thread
def print_hello(interval_secs: int = 3):
    while True:
        print('Hello')
        time_sleep(interval_secs)


if __name__ == '__main__':
    print_hello()
    time_sleep(5)
    stop_thread(print_hello.__name__)
    time_sleep(15)
    print("finish...")
