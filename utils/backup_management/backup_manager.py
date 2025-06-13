from database import db
from models import BackupSetting
from models.models import get_current_nsk_time
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

    def run(self):
        """
        метод для обработки событий в отдельном треде (потоке), а именно
        сохранение бэкапов в заданные (backup_local_dir, backup_lan_dir) каталоги (если они не существуют,
        то попробовать их предварительно создать).

        Алгоритм работы:
        1) каждый заданный период времени (period_secs) происходит пробуждение.
        берутся все пользователи (таблица БД user) и проверяется, что последняя активность (поле last_activity_at)
        каждого из них была более 1 часа назад по сравнению с текущим временем (проверяется с помощью функции
        get_current_nsk_time). если все были активны более 1 часа назад - запускается следующий этап, если нет, то
        спустя таймаут (check_period_secs) проверяется снова - и так заданное количество рвз (check_times). по
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
        таблиц берем с помощью - сам найди способ, наверное какойто SQL-запрос...
        4) в случае успешного сохранения хотя бы в одну из папок необходимо сделать соответствующую запись
        в таблицу backup_log БД (поля таблицы:
        id = db.Column(Integer, primary_key=True)
        started_at = db.Column(DateTime(timezone=True), default=get_current_nsk_time, nullable=False)
        ended_at = db.Column(DateTime(timezone=True), nullable=True)
        is_successful = db.Column(Boolean, default=False, nullable=False)
        total_size_mb = db.Column(Integer, default=0, nullable=False)
        backup_setting_id = db.Column(Integer, db.ForeignKey('backup_settings.id'), nullable=False)
        backup_setting = db.relationship('BackupSetting', back_populates='backup_log'))
        5) ожидание по большому таймауту.

        Время жизни бэкапов (lifespan_days) - используем для автоудаления (текущая дата - дата в названии папок)
        при превышении lifespan_days должно происходить автоудаление подпапок из обоих директорий.
        :return:
        """
        setting = self.get_active_backup_setting()
        name = setting.name
        period_secs = setting.period_secs
        check_period_secs = setting.check_period_secs
        check_times = setting.check_times
        backup_local_dir = setting.backup_local_dir
        backup_lan_dir = setting.backup_lan_dir
        lifespan_days = setting.lifespan_days
        time_now = get_current_nsk_time()

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

    @staticmethod
    def restore_db_tables():
        """
        Восстановление всех таблиц БД из заданного бэкапа.
        проверка наличия файлов сначала из локалльной папки, затем сетевой.
        проверка на то, что все таблицы БД были предварительно очищены (с помощью статик метода drop_db_tables)
        реализация процесса восстановления данных во всех таблицах БД
        :return:
        """
        pass
