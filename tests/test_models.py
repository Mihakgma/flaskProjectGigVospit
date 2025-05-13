import pytest
from sqlalchemy import create_engine, Column, String, Integer, DateTime  # Добавили DateTime
from sqlalchemy.orm import sessionmaker, declarative_base
from datetime import datetime, timezone  # Добавили datetime и timezone
import pytz  # Если используете pytz для вашей целевой зоны

# 1. Создаем новую декларативную базу СПЕЦИАЛЬНО для этих тестов
TestBase = declarative_base()

# Если вы используете pytz для целевой временной зоны (например, Новосибирск)
# Убедитесь, что эти определения есть в test_models.py
TARGET_TIMEZONE_STR = 'Asia/Novosibirsk'  # или 'Europe/Moscow', или другая
TARGET_TIMEZONE = pytz.timezone(TARGET_TIMEZONE_STR)


def get_current_time_in_target_zone():
    """Возвращает текущее время в целевой временной зоне."""
    return datetime.now(TARGET_TIMEZONE)


def get_current_time_utc():
    """Возвращает текущее время в UTC."""
    return datetime.now(timezone.utc)


# 2. Определяем тестовый базовый класс
class IsolatedBaseModel(TestBase):
    __abstract__ = True
    id = Column(Integer, primary_key=True)

    # Добавляем поля DateTime, как они могут быть в вашем реальном BaseModel
    # Используйте ОДИН из вариантов ниже для default (get_current_time_utc или get_current_time_in_target_zone)
    # Важно, чтобы функция была доступна.

    # Вариант 1: Используем UTC (проще для тестов, если не тестируется сама временная зона)
    created_at = Column(DateTime(timezone=True), default=get_current_time_utc)
    updated_at = Column(DateTime(timezone=True), default=get_current_time_utc, onupdate=get_current_time_utc)

    # Вариант 2: Используем вашу целевую временную зону (если это важно для теста)
    # created_at = Column(DateTime(timezone=True), default=get_current_time_in_target_zone)
    # updated_at = Column(DateTime(timezone=True), default=get_current_time_in_target_zone, onupdate=get_current_time_in_target_zone)

    def __repr__(self):
        parts = [f"id={self.id}"]
        if hasattr(self, 'name') and getattr(self, 'name') is not None:
            parts.append(f"name='{str(getattr(self, 'name'))}'")
        # Вы можете добавить created_at в repr для отладки, если хотите
        # if hasattr(self, 'created_at') and self.created_at is not None:
        #     parts.append(f"created_at='{self.created_at.isoformat()}'")
        return f"<{self.__class__.__name__}({', '.join(parts)})>"


@pytest.fixture(scope="function")
def isolated_test_session():
    engine = create_engine("sqlite:///:memory:")
    TestBase.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()
    TestBase.metadata.drop_all(engine)


class TestIsolatedBaseModelRepr:
    def test_repr_with_name_attribute(self, isolated_test_session):
        class TestRole(IsolatedBaseModel):
            __tablename__ = 'test_roles_table'
            name = Column(String(50))

        TestRole.__table__.create(isolated_test_session.bind, checkfirst=True)

        role = TestRole(id=1, name="Admin")
        print(*[(k, v) for (k, v) in role.__dict__.items()], sep="\n")
        isolated_test_session.add(role)
        isolated_test_session.commit()  # Здесь возникает ошибка, если created_at/updated_at некорректны
        expected_output = "<TestRole(id=1, name='Admin')>"
        assert str(role) == expected_output

    def test_repr_without_name_attribute(self, isolated_test_session):
        class TestOtherClass(IsolatedBaseModel):
            __tablename__ = 'test_other_classes_table'

        TestOtherClass.__table__.create(isolated_test_session.bind, checkfirst=True)

        other_instance = TestOtherClass(id=2)
        isolated_test_session.add(other_instance)
        isolated_test_session.commit()
        expected_output = "<TestOtherClass(id=2)>"
        assert str(other_instance) == expected_output

    def test_repr_with_id_only(self, isolated_test_session):
        class TestSimple(IsolatedBaseModel):
            __tablename__ = 'test_simple_table_name'  # ИСПРАВЛЕНО (было tablename)

        # ИСПРАВЛЕНО (было TestSimple.table.create)
        TestSimple.__table__.create(isolated_test_session.bind, checkfirst=True)

        simple_instance = TestSimple(id=3)
        isolated_test_session.add(simple_instance)
        isolated_test_session.commit()

        expected_output = "<TestSimple(id=3)>"
        assert str(simple_instance) == expected_output
