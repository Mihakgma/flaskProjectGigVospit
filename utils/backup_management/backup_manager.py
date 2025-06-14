from __future__ import annotations

import os
import shutil
import time
import json
import threading
from datetime import datetime, timedelta
from typing import List, Tuple

from flask import flash
from sqlalchemy import text, inspect, func
from sqlalchemy.orm import Session

from database import db
from models import BackupSetting, User, BackupLog
from models.models import get_current_nsk_time  # Убедитесь, что импорт корректен
from utils.backup_management import Singleton


class BackupManager(Singleton, threading.Thread):  # Наследование от Singleton и threading.Thread
    """
    Осуществляет сохранение таблиц БД и их восстановление из сохраненных файлов.

    Необходимо:
    1) заполнить функционал созданных методов с учетом док-строк внутри каждого;
    2) наследовать класс от Treading для работы с объектом класса (Singleton) в отдельном потоке.
    """

    def __init__(self, *args, **kwargs):
        # Инициализация потока, daemon=True чтобы поток завершался вместе с основным приложением
        threading.Thread.__init__(self, *args, daemon=True,
                                  **kwargs)
        self.__active_backup_setting: BackupSetting | None = None
        self.is_running = False  # Флаг для управления потоком

    def init(self,
             active_backup_setting: BackupSetting,
             ):
        """
        Инициализирует объект BackupManager.
        """
        if active_backup_setting is None and self.__active_backup_setting:
            pass
        else:
            self.__active_backup_setting = active_backup_setting

    def get_active_backup_setting(self) -> BackupSetting | None:
        """
        Возвращает текущую активную настройку резервного копирования.
        """
        return self.__active_backup_setting

    def set_active_backup_setting(self, active_backup_setting: BackupSetting):
        """
        Устанавливает новую активную настройку резервного копирования.

        Args:
            active_backup_setting: Объект BackupSetting.

        Raises:
            TypeError: Если переданный объект не является экземпляром BackupSetting.
        """
        if not isinstance(active_backup_setting, BackupSetting):
            raise TypeError(f'Object <{active_backup_setting}> is not of type <{BackupSetting}>')
        self.__active_backup_setting = active_backup_setting

    active_backup_setting = property(get_active_backup_setting, set_active_backup_setting)

    def run(self):
        """
        Метод для обработки событий в отдельном потоке, а именно
        сохранение бэкапов в заданные (backup_local_dir, backup_lan_dir) каталоги (если они не существуют,
        то попробовать их предварительно создать).

        Алгоритм работы:
        1) каждый заданный период времени (period_secs) происходит пробуждение.
        берутся все пользователи (таблица БД user) и проверяется, что последняя активность (поле last_activity_at)
        каждого из них была более 1 часа назад по сравнению с текущим временем (проверяется с помощью функции
        get_current_nsk_time). если все были активны более 1 часа назад - запускается следующий этап, если нет, то
        спустя таймаут (check_period_secs) проверяется снова - и так заданное количество раз (check_times). по
        истечению заданного количества проверок (check_times) и таймаутов между ними (check_period_secs) -
        не был запущен следующий этап, то запускается ожидание по большому тайтауту (period_secs).
        2) следующий этап. проверка существования заданных (backup_local_dir, backup_lan_dir) каталогов
        (если они не существуют, то попробовать их предварительно создать). в случае, если не получается их создать -
        ошибка (сам выбери тип ошибки и корректное ее описание). если получилось создать хотя бы один из каталогов идем
        на
        3) следующий этап - попытка создания подкаталога в каждом каталоге (или хотя бы в одном из них)
        папки с текущей датой (ДД.ММ.ГГГГ), если папка с текущей датой уже существует и она не пустая (там есть файлы
        с названиями всех таблиц БД в формате json), то скипаем папку (напр., backup_local_dir) и переходим к следующей
        (напр., backup_lan_dir). проверяем по той же схеме. если условия для перехода на следующий этап удовлетворяют
        хотя бы для одной директории, то переходим к нему, иначе - ожидание по большому таймауту (period_secs).
        3) сохраняем содержимое всех таблиц в формате json в файлах с соответствующим названием. названия
        таблиц берем с помощью - сам найди способ, наверное какой-то SQL-запрос...
        4) в случае успешного сохранения хотя бы в одну из папок необходимо сделать соответствующую запись
        в таблицу backup_log БД (поля таблицы:
        id = db.Column(Integer, primary_key=True)
        started_at = db.Column(DateTime(timezone=True), default=get_current_nsk_time, nullable=False)
        ended_at = db.Column(DateTime(timezone=True), nullable=True)
        is_successful = db.Column(Boolean, default=False, nullable=False)
        total_size_mb = db.Column(Integer, default=0, nullable=False)
        backup_setting_id = db.Column(Integer, db.ForeignKey('backup_settings.id'), nullable=False)
        """
        self.is_running = True  # Устанавливаем флаг, что поток запущен
        while self.is_running:
            if not self.active_backup_setting:
                time.sleep(60)  # Ждем немного, если нет активной настройки, чтобы не нагружать процессор
                continue

            try:
                if self._check_users_activity():
                    self._perform_backup()
                else:
                    self._wait_for_activity()
            except Exception as e:
                print(f"An error occurred in BackupManager: {e}")
            finally:
                time.sleep(self.active_backup_setting.period_secs)

    def _check_users_activity(self) -> bool:
        """
        Проверяет, была ли активность пользователей более 1 часа назад.
        """
        check_times = self.active_backup_setting.check_times
        check_period_secs = self.active_backup_setting.check_period_secs

        for _ in range(check_times):
            if self._is_all_users_inactive():
                return True
            time.sleep(check_period_secs)
        return False

    def _is_all_users_inactive(self) -> bool:
        """
        Проверяет, все ли пользователи неактивны более 1 часа назад, используя ORM.
        """
        one_hour_ago = get_current_nsk_time() - timedelta(hours=1)
        with db.session.begin() as session:  # Use db.session
            inactive_users_count = session.query(func.count(User.id)).filter(
                User.last_activity_at > one_hour_ago).scalar()  # Используем scalar() для получения одного значения
        return inactive_users_count == 0

    def _wait_for_activity(self):
        """
        Ожидает period_secs перед следующей попыткой проверки активности.
        """
        print("All users not inactive. Waiting for activity...")
        time.sleep(self.active_backup_setting.period_secs)

    def _perform_backup(self):
        """
        Выполняет резервное копирование.
        """
        setting = BackupSetting.query.get(self.active_backup_setting.id)
        self.set_active_backup_setting(active_backup_setting=setting)
        backup_setting = self.active_backup_setting
        flash(f'Backup setting: {backup_setting}', 'success')
        started_at = get_current_nsk_time()
        is_successful = False
        total_size_mb = 0
        try:
            backup_paths = self._prepare_backup_directories()
            if not backup_paths:
                raise OSError("Не удалось подготовить ни одну из директорий для бэкапа.")

            # Получаем имена таблиц
            table_names = self._get_table_names()

            # Бэкапим в каждую директорию, где это возможно
            backup_results: List[Tuple[str, bool, int]] = []  # Список кортежей (путь_к_директории, success, размер_мб)
            for backup_dir in backup_paths:
                try:
                    backup_success, size_mb = self._backup_tables_to_directory(backup_dir, table_names)
                    backup_results.append((backup_dir, backup_success, size_mb))
                except Exception as e:
                    print(f"Ошибка при создании бэкапа в {backup_dir}: {e}")
                    backup_results.append((backup_dir, False, 0))

            # Определяем общий успех и размер
            is_successful = any(result[1] for result in backup_results)  # Если хоть один успешен, то общий успех
            total_size_mb = sum(result[2] for result in backup_results)  # Суммируем размеры

        except Exception as e:
            print(f"An error occurred during the backup process: {e}")
        finally:
            self._log_backup(started_at, is_successful, total_size_mb, backup_setting.id)
            self._cleanup_old_backups()

    def _prepare_backup_directories(self) -> List[str]:
        """
        Подготавливает директории для резервного копирования:
        - Проверяет существование локальной и сетевой директорий.
        - Пытается создать директории, если они не существуют.
        - Создает поддиректорию с текущей датой.

        Returns:
            List[str]: Список путей к подготовленным директориям для резервного копирования.
                       Возвращает пустой список, если ни одну директорию не удалось подготовить.
        """
        backup_setting = self.active_backup_setting
        backup_dirs: List[str] = []
        date_str = datetime.now().strftime("%d.%m.%Y")

        for base_dir in [backup_setting.backup_local_dir, backup_setting.backup_lan_dir]:
            if not base_dir:
                continue  # Пропускаем, если путь не указан

            try:
                if not os.path.exists(base_dir):
                    try:
                        os.makedirs(base_dir)
                        print(f"Создана директория: {base_dir}")
                    except OSError as e:
                        print(f"Ошибка при создании директории {base_dir}: {e}")
                        continue  # Не удалось создать базовую директорию, пропускаем

                # Создаем поддиректорию с датой
                date_dir = os.path.join(base_dir, date_str)
                if not os.path.exists(date_dir):
                    try:
                        os.makedirs(date_dir)
                        print(f"Создана директория: {date_dir}")
                    except OSError as e:
                        print(f"Ошибка при создании директории {date_dir}: {e}")
                        continue  # Не удалось создать datedir, пропускаем

                # Проверка на наличие файлов в date_dir. Считаем директорию пустой, если там нет файлов
                if not os.listdir(date_dir):
                    backup_dirs.append(date_dir)
                else:
                    print(f"Директория {date_dir} уже существует и не пуста. Пропускаем.")

            except Exception as e:
                print(f"Ошибка при подготовке директории {base_dir}: {e}")
        return backup_dirs

    def _get_table_names(self) -> List[str]:
        """
        Получает список названий таблиц в базе данных.

        Returns:
            List[str]: Список названий таблиц.
        """
        inspector = inspect(db.engine)
        return inspector.get_table_names()

    def _backup_tables_to_directory(self, directory: str, table_names: List[str]) -> Tuple[bool, int]:
        """
        Сохраняет содержимое всех таблиц в формате JSON в указанную директорию.

        Args:
            directory: Путь к директории, куда сохранять бэкапы.
            table_names: Список названий таблиц для бэкапа.

        Returns:
            Tuple[bool, int]: (Успех операции, размер_в_мб)
        """
        total_size_mb = 0
        success = True
        session: Session = db.session  # Получаем сессию SQLAlchemy

        for table_name in table_names:
            try:
                # Получаем данные из таблицы
                query = text(f"SELECT * FROM {table_name}")
                result = session.execute(query)
                data = [dict(row) for row in result.mappings().all()]  # Получаем данные в формате list of dicts

                # Сохраняем данные в JSON-файл
                file_path = os.path.join(directory, f"{table_name}.json")
                with open(file_path, "w", encoding="utf-8") as f:
                    json.dump(data, f, indent=4, ensure_ascii=False)

                # Подсчитываем размер файла
                file_size_bytes = os.path.getsize(file_path)
                total_size_mb += file_size_bytes / (1024 * 1024)

                print(f"Backup of table '{table_name}' saved to {file_path}")

            except Exception as e:
                print(f"Error backing up table '{table_name}': {e}")
                success = False
        return success, int(total_size_mb)

    def _log_backup(self, started_at: datetime, is_successful: bool, total_size_mb: int, backup_setting_id: int):
        """
        Создает запись в таблице backup_log.
        """
        ended_at = get_current_nsk_time()
        backup_log = BackupLog(
            started_at=started_at,
            ended_at=ended_at,
            is_successful=is_successful,
            total_size_mb=total_size_mb,
            backup_setting_id=backup_setting_id,
        )
        try:
            db.session.add(backup_log)
            db.session.commit()
            print(f"Backup log created. Success: {is_successful}, Size: {total_size_mb}MB")
        except Exception as e:
            db.session.rollback()
            print(f"Error creating backup log: {e}")

    def _cleanup_old_backups(self):
        """
        Удаляет старые резервные копии в соответствии с параметром lifespan_days.
        Также удаляет соответствующие записи из backup_log.
        """
        backup_setting = self.active_backup_setting
        if not backup_setting or backup_setting.lifespan_days is None:
            print("No active backup setting or lifespan_days not set. Skipping cleanup.")
            return

        lifespan_days = backup_setting.lifespan_days
        cutoff_date = get_current_nsk_time() - timedelta(
            days=lifespan_days)  # Вычисляем дату, после которой файлы удаляются

        # Получаем все логи бэкапов, которые необходимо удалить
        with db.session.begin() as session:
            old_backup_logs = session.query(BackupLog).filter(BackupLog.started_at < cutoff_date,
                                                              BackupLog.backup_setting_id == backup_setting.id).all()
            backup_log_ids_to_delete = [log.id for log in old_backup_logs]

        # Удаляем соответствующие записи из backup_log
        with db.session.begin() as session:
            for log in old_backup_logs:
                session.delete(log)
            session.commit()
            print(f"Removed {len(old_backup_logs)} old backup logs.")

        # Удаляем директории и файлы
        for base_dir in [backup_setting.backup_local_dir, backup_setting.backup_lan_dir]:
            if not base_dir or not os.path.isdir(base_dir):
                continue  # Пропускаем некорректные пути или несуществующие директории

            try:
                for item in os.listdir(base_dir):
                    item_path = os.path.join(base_dir, item)
                    if os.path.isdir(item_path):
                        try:
                            # Пытаемся преобразовать имя папки в дату
                            date_obj = datetime.strptime(item, "%d.%m.%Y")
                            if date_obj < cutoff_date:  # Если дата папки старше, чем cutoff_date
                                try:
                                    shutil.rmtree(item_path)  # Удаляем директорию и все ее содержимое
                                    print(f"Removed directory: {item_path}")
                                except OSError as e:
                                    print(f"Error removing directory {item_path}: {e}")
                        except ValueError:
                            # Обрабатываем случаи, когда имя папки не соответствует формату даты
                            print(f"Skipping directory {item_path} - invalid date format.")
            except OSError as e:
                print(f"Error listing directory {base_dir}: {e}")

    def stop(self):
        """
        Останавливает поток.
        """
        self.is_running = False
        print("BackupManager is stopping...")


# --- Пример использования (необходимо для работы) ---
if __name__ == '__main__':
    # Пример:
    # 1. Настройка приложения Flask (app = create_app()) -- пропустим, т.к. у тебя уже есть
    # 2. Инициализация БД (db.create_all()) -- тоже пропустим
    # 3. Создание BackupSetting (или получение из БД)
    # 4. Создание и запуск BackupManager

    # --- Пример создания BackupSetting (замените значения) ---
    from app import create_app  # Assuming app.py or similar

    app = create_app()
    with app.app_context():
        # Ensure the database is created and initialized
        db.create_all()  # Create all tables (if they don't exist)

        # Create a dummy BackupSetting (or retrieve from DB)
        # Replace with your actual values from the models.py
        try:
            new_setting = BackupSetting(
                name="Test Backup",
                period_secs=60,
                check_period_secs=10,
                check_times=3,
                backup_local_dir="C:\\temp\\backups_test",  # Замените на реальный путь
                backup_lan_dir="",  # Или укажите путь
                is_active_now=True,
                lifespan_days=7,
            )
            db.session.add(new_setting)
            db.session.commit()
            active_setting = new_setting  # Use the newly created setting
            print("BackupSetting created/retrieved successfully")
        except Exception as e:
            print(f"Error creating/retrieving BackupSetting: {e}")
            active_setting = BackupSetting.query.filter_by(
                name="Test Backup").first()  # Попытка получить существующую запись, чтобы не было проблем
            if not active_setting:
                print("Не удалось получить существующую запись, прекращаем выполнение примера.")
                exit()

    # 5. Создание и запуск BackupManager
    manager = BackupManager()
    with app.app_context():
        manager.init(active_setting)
        manager.start()
        print("BackupManager started.")

        # --- Чтобы остановить BackupManager (например, через некоторое время) ---
        time.sleep(60)  # Run for 60 seconds (example)
        manager.stop()
        manager.join()  # Wait for the thread to finish

        print("BackupManager stopped.")
