from database import db
from models import BackupSetting
from utils.backup_management import Singleton


class BackupManager(Singleton):
    """
    Осуществляет сохранение таблиц БД и их восстановление из сохраненных файлов.

    Необходимо:
    1) заполнить функционал созданных методов с учетом док-строк внутри каждого;
    2) наследовать класс от Treading для работы с объектом класса (Singleton) в отдельном потоке.
    """

    def __init__(self,
                 active_backup_setting: BackupSetting,
                 ):
        if active_backup_setting is None and self.__active_backup_setting:
            pass
        else:
            self.__active_backup_setting = active_backup_setting

    def get_active_backup_setting(self) -> BackupSetting:
        return self.__active_backup_setting

    def set_active_backup_setting(self, active_backup_setting: BackupSetting):
        if not isinstance(active_backup_setting, BackupSetting):
            raise TypeError(f'Object <{active_backup_setting}> is not of type <{BackupSetting}>')
        self.__active_backup_setting = active_backup_setting

    active_backup_setting = property(get_active_backup_setting, set_active_backup_setting)

    def store_backup(self):
        setting = self.get_active_backup_setting()
        name = setting.name
        period_secs = setting.period_secs
        check_period_secs = setting.check_period_secs
        check_times = setting.check_times
        backup_local_dir = setting.backup_local_dir
        backup_lan_dir = setting.backup_lan_dir
        lifespan_days = setting.lifespan_days

    @staticmethod
    def get_instance():
        active_backup_setting = BackupSetting.query.filter(BackupSetting.active).first()
        return BackupManager(active_backup_setting=active_backup_setting)

    @staticmethod
    def drop_db_tables():
        query = """
                    DO $$
            DECLARE
                r RECORD;
            BEGIN
                -- Получаем все таблицы из схемы 'public' (или другой нужной схемы)
                FOR r IN (SELECT tablename FROM pg_tables WHERE schemaname = 'public') LOOP
                    -- Динамически формируем и выполняем команду DROP TABLE
                    -- CASCADE удалит также все зависимые объекты (ограничения, индексы и т.д.)
                    -- и таблицы, которые ссылаются на удаляемую через внешние ключи.
                    -- Если вы не хотите каскадного удаления, используйте RESTRICT (и убедитесь, что нет зависимостей).
                    EXECUTE 'DROP TABLE IF EXISTS public.' || quote_ident(r.tablename) || ' CASCADE';
                END LOOP;
            END $$;
        """
        db.session.execute(query)
        db.session.commit()
