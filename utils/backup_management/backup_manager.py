from __future__ import annotations

import os
import shutil
import time
import json
import threading
from datetime import datetime, timedelta
from typing import List, Tuple, Optional

from flask import flash, current_app, g
from sqlalchemy import text, inspect, func
from sqlalchemy.exc import OperationalError, SQLAlchemyError

# from sqlalchemy.orm import Session

from database import db
from models import BackupSetting, User, BackupLog
from models.models import get_current_nsk_time
from utils.backup_management import Singleton


class BackupManager(Singleton):  # Наследование от Singleton и threading.Thread
    """
    Осуществляет сохранение таблиц БД и их восстановление из сохраненных файлов.

    Необходимо:
    1) заполнить функционал созданных методов с учетом док-строк внутри каждого;
    2) наследовать класс от Treading для работы с объектом класса (Singleton) в отдельном потоке.
    """

    def __init__(self,
                 active_backup_setting,
                 testing: bool = False):
        self.testing = testing
        self.__active_backup_setting: BackupSetting | None = active_backup_setting
        self.is_running = False  # Флаг для управления потоком
        self._thread: Optional[threading.Thread] = None

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

    def _run_loop(self):
        self.is_running = True
        print('Backup manager starting ...')
        counter = -1
        while self.is_running:
            counter += 1
            if counter == 0:
                time.sleep(10)
            elif not self.__active_backup_setting:
                print('Active backup setting is disabled or has been removed...')
                time.sleep(60)
                continue
            try:
                with self.Session() as session:
                    print('Trying check users last activity...')
                    setting = self.__active_backup_setting  # получаем setting здесь
                    if self._check_users_activity(setting):  # передаем setting сюда
                        print('Checked: users last activity > 1 hour ago.')
                        self._perform_backup(setting)  # передаем setting сюда
                        print('Backup has been performed.')
                    else:
                        print('Checked: users last activity < 1 hour ago. Waiting...')
                        self._wait_for_activity()
            except (OperationalError, SQLAlchemyError) as e:
                print(f"SQLAlchemy error in BackupManager: {e}")
                time.sleep(60)
            except Exception as e:
                print(f"An error occurred in BackupManager: {e}")
            finally:
                if self.__active_backup_setting:
                    time.sleep(self.__active_backup_setting.period_secs)

    def _check_users_activity(self,
                              backup_setting: BackupSetting) -> bool:
        """
        Проверяет, была ли активность пользователей более 1 часа назад.
        """
        check_times = backup_setting.check_times
        check_period_secs = backup_setting.check_period_secs
        print('Activity variables have been successfully got from BackupSetting obj')
        i = 0
        for _ in range(check_times):
            i += 1
            print(f'Checking users last activity N = <{i}>.')
            if self._is_all_users_inactive():
                print(f'All users are inactive for 1 hour ago.')
                return True
            time.sleep(check_period_secs)
        return False

    def _is_all_users_inactive(self) -> bool:
        """
        Проверяет, все ли пользователи неактивны более 1 часа назад, используя ORM.
        """
        # with self.flask_app.app_context():
        if self.testing:
            five_minutes_ago = get_current_nsk_time() - timedelta(minutes=5)
            inactive_users_count = g.db.session.query(func.count(User.id)).filter(  # Исправлено здесь
                User.last_activity_at > five_minutes_ago).scalar()  # Используем scalar() для получения одного значения
        else:
            one_hour_ago = get_current_nsk_time() - timedelta(hours=1)
            inactive_users_count = g.db.session.query(func.count(User.id)).filter(  # Исправлено здесь
                User.last_activity_at > one_hour_ago).scalar()  # Используем scalar() для получения одного значения
        return inactive_users_count == 0

    def _wait_for_activity(self):
        """
        Ожидает period_secs перед следующей попыткой проверки активности.
        """
        print("All users not inactive. Waiting for activity...")
        time.sleep(self.active_backup_setting.period_secs)

    def _perform_backup(self, backup_setting: BackupSetting):
        """Выполняет резервное копирование."""
        started_at = get_current_nsk_time()
        is_successful = False
        total_size_mb = 0
        try:
            backup_paths = self._prepare_backup_directories(backup_setting)  # Передали setting сюда
            if not backup_paths:
                raise OSError("Не удалось подготовить ни одну из директорий для бэкапа.")

            table_names = self._get_table_names()

            backup_results = []
            for backup_dir in backup_paths:
                try:
                    backup_success, size_mb = self._backup_tables_to_directory(backup_dir, table_names)
                    backup_results.append((backup_dir, backup_success, size_mb))
                except Exception as e:
                    print(f"Ошибка при создании бэкапа в {backup_dir}: {e}")
                    backup_results.append((backup_dir, False, 0))

            is_successful = any(result[1] for result in backup_results)
            total_size_mb = sum(result[2] for result in backup_results)

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
        # with self.flask_app.app_context():
        total_size_mb = 0
        success = True
        # session: Session = db.session  # Получаем сессию SQLAlchemy

        for table_name in table_names:
            try:
                # Получаем данные из таблицы
                query = text(f"SELECT * FROM {table_name}")
                result = db.execute(query)
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
        # with self.flask_app.app_context():
        ended_at = get_current_nsk_time()
        backup_log = BackupLog(
            started_at=started_at,
            ended_at=ended_at,
            is_successful=is_successful,
            total_size_mb=total_size_mb,
            backup_setting_id=backup_setting_id,
        )
        try:
            g.db.session.add(backup_log)
            g.db.session.commit()
            print(f"Backup log created. Success: {is_successful}, Size: {total_size_mb}MB")
        except Exception as e:
            g.db.session.rollback()
            print(f"Error creating backup log: {e}")

    def _cleanup_old_backups(self):
        """
        Удаляет старые резервные копии в соответствии с параметром lifespan_days.
        Также удаляет соответствующие записи из backup_log.
        """
        # with self.flask_app.app_context():
        backup_setting = self.active_backup_setting
        if not backup_setting or backup_setting.lifespan_days is None:
            print("No active backup setting or lifespan_days not set. Skipping cleanup.")
            return

        lifespan_days = backup_setting.lifespan_days
        cutoff_date = get_current_nsk_time() - timedelta(
            days=lifespan_days)  # Вычисляем дату, после которой файлы удаляются

        # Получаем все логи бэкапов, которые необходимо удалить
        # with db.session.begin() as session:
        old_backup_logs = BackupLog.query.filter(BackupLog.started_at < cutoff_date,
                                                 BackupLog.backup_setting_id == backup_setting.id).all()
        backup_log_ids_to_delete = [log.id for log in old_backup_logs]

        # Удаляем соответствующие записи из backup_log
        with g.db.session.begin() as session:
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

    def start(self):
        """Запускает бэкап в фоновом режиме."""
        if not self.is_running:
            # with app.app_context():
            self.is_running = True
            try:
                self._thread = threading.Thread(target=self._run_loop,
                                                daemon=True)
                self._thread.start()
            except BaseException as e:
                print(f'Error has been happened during starting backup manager object: {e}')

    def stop(self):
        """Останавливает бэкап-менеджер."""
        self.is_running = False
        if self._thread:
            self._thread.join(timeout=1)
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
            g.db.session.add(new_setting)
            g.db.session.commit()
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
    manager = BackupManager(active_backup_setting=active_setting)
    with app.app_context():
        manager.start()
        print("BackupManager started.")
        # --- Чтобы остановить BackupManager (например, через некоторое время) ---
        time.sleep(60)  # Run for 60 seconds (example)
        manager.stop()
        manager.join()  # Wait for the thread to finish

        print("BackupManager stopped.")
