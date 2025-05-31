import sys


def check_lock_info_names(obj):
    if not type(obj) is str:
        raise TypeError('obj must be a string')
    if len(obj) == 0:
        raise ValueError('obj cannot be an empty string')


def check_ids(obj):
    if not type(obj) is int:
        raise TypeError('id must be an integer')
    if obj < 1:
        raise ValueError('id value must be greater than 0')


class LockInfo:
    """
    A class to hold information about a lock.

    Need to override methods below:
    - hash,
    - equals,
    - repr / toString (???)

    Also need to add little tests for current class work in if name == main block!!!
    """
    def __init__(self,
                 blueprint_name: str,
                 function_name: str,
                 edited_table_id: int,
                 user_id: int):
        self.__blueprint_name = blueprint_name
        self.__function_name = function_name
        self.__edited_table_id = edited_table_id
        self.__user_id = user_id

    def get_blueprint_name(self):
        return self.__blueprint_name

    def get_function_name(self):
        return self.__function_name

    def get_edited_table_id(self):
        return self.__edited_table_id

    def get_user_id(self):
        return self.__user_id

    def set_blueprint_name(self, blueprint_name: str) -> None:
        check_lock_info_names(blueprint_name)
        if not blueprint_name.endswith('_bp'):
            raise ValueError('blueprint_name must end with _bp')
        self.__blueprint_name = blueprint_name

    def set_function_name(self, function_name: str) -> None:
        check_lock_info_names(function_name)
        self.__function_name = function_name

    def set_edited_table_id(self, edited_table_id: int) -> None:
        check_ids(edited_table_id)
        self.__edited_table_id = edited_table_id

    def set_user_id(self, user_id: int) -> None:
        check_ids(user_id)
        self.__user_id = user_id

    blueprint_name = property(get_blueprint_name, set_blueprint_name, "Property for blueprint_name")
    function_name = property(get_function_name, set_function_name, "Property for function_name")
    edited_table_id = property(get_edited_table_id, set_edited_table_id,
                               "Property for edited_table_id")
    user_id = property(get_user_id, set_user_id, "Property for user_id")

    def funct_tablerow_equivalence(self, other):
        """
        Проверка на эквивалентность без сравнения пользователя!
        :param other:
        :return:
        """
        if not isinstance(other, LockInfo):
            return NotImplemented  # Или return False; NotImplemented - более строгий подход для операторов
        return (self.__blueprint_name == other.__blueprint_name and
                self.__function_name == other.__function_name and
                self.__edited_table_id == other.__edited_table_id)

    def __eq__(self, other):
        """
        Переопределение оператора равенства (==).
        Два объекта LockInfo считаются равными, если все их четыре поля совпадают.
        """
        if not isinstance(other, LockInfo):
            return NotImplemented  # Или return False; NotImplemented - более строгий подход для операторов
        return (self.__blueprint_name == other.__blueprint_name and
                self.__function_name == other.__function_name and
                self.__edited_table_id == other.__edited_table_id and
                self.__user_id == other.__user_id)

    def __hash__(self):
        """
        Переопределение метода хеширования.
        Обязательно при переопределении __eq__, чтобы объекты можно было использовать
        в хешируемых коллекциях (например, set, dict).
        Хеш-значение должно быть основано на тех же полях, что и __eq__.
        """
        return hash((self.__blueprint_name,
                     self.__function_name,
                     self.__edited_table_id,
                     self.__user_id))

    def __repr__(self):
        """
        Переопределение строкового представления объекта (repr).
        Позволяет получить однозначное представление объекта, часто пригодное
        для воссоздания его.
        """
        return (f"LockInfo(blueprint_name='{self.__blueprint_name}', "
                f"function_name='{self.__function_name}', "
                f"edited_table_id={self.__edited_table_id}, "
                f"user_id={self.__user_id})")


# --- Тесты для класса LockInfo ---
if __name__ == '__main__':
    print("--- Тестирование класса LockInfo ---")

    # 1. Тестирование инициализации
    print("\n1. Тестирование инициализации и свойств:")
    try:
        lock1 = LockInfo("applicants_bp", "add_applicant", 1, 101)
        print(f"Создан lock1: {lock1}")
        print(f"lock1.blueprint_name: {lock1.blueprint_name}")
        print(f"lock1.user_id: {lock1.user_id}")

        lock1.set_function_name("edit_applicant")
        print(f"lock1 после изменения function_name: {lock1}")

        # Тестирование невалидных значений при инициализации
        try:
            LockInfo("invalid_bp", "func", 1, 1)
        except ValueError as e:
            print(f"Ожидаемая ошибка при создании LockInfo с неверным blueprint_name: {e}")

        try:
            LockInfo("users_bp", "func", 0, 1)
        except ValueError as e:
            print(f"Ожидаемая ошибка при создании LockInfo с неверным edited_table_id: {e}")

        try:
            LockInfo("users_bp", "func", 1, "abc")
        except TypeError as e:
            print(f"Ожидаемая ошибка при создании LockInfo с неверным типом user_id: {e}")

    except Exception as e:
        print(f"Неожиданная ошибка при инициализации: {e}")
        sys.exit(1)

    # 2. Тестирование __eq__ (равенство)
    print("\n2. Тестирование __eq__:")
    lock2 = LockInfo("applicants_bp", "add_applicant", 1, 101)  # Идентичен lock1 на момент создания
    lock3 = LockInfo("applicants_bp", "add_applicant", 2, 101)  # Отличается edited_table_id
    lock4 = LockInfo("applicants_bp", "add_application", 1, 101)  # Отличается function_name
    lock5 = LockInfo("users_bp", "add_applicant", 1, 101)  # Отличается blueprint_name
    lock6 = LockInfo("applicants_bp", "add_applicant", 1, 102)  # Отличается user_id

    print(f"lock1: {lock1}")
    print(f"lock2: {lock2}")
    print(f"lock3: {lock3}")
    print(f"lock4: {lock4}")
    print(f"lock5: {lock5}")
    print(f"lock6: {lock6}")

    print(f"lock1 == lock2: {lock1 == lock2} (Ожидаемо: True)")
    print(f"lock1 == lock3: {lock1 == lock3} (Ожидаемо: False)")
    print(f"lock1 != lock3: {lock1 != lock3} (Ожидаемо: True)")
    print(f"lock1 == lock4: {lock1 == lock4} (Ожидаемо: False)")
    print(f"lock1 == lock5: {lock1 == lock5} (Ожидаемо: False)")
    print(f"lock1 == lock6: {lock1 == lock6} (Ожидаемо: False)")
    print(f"lock1 == 'some_string': {lock1 == 'some_string'} (Ожидаемо: False/NotImplemented)")

    # 3. Тестирование __hash__
    print("\n3. Тестирование __hash__:")
    print(f"Хеш lock1: {hash(lock1)}")
    print(f"Хеш lock2: {hash(lock2)}")
    print(f"Хеш lock3: {hash(lock3)}")
    print(f"Хеш lock4: {hash(lock4)}")

    print(f"Хеш lock1 == Хеш lock2: {hash(lock1) == hash(lock2)} (Ожидаемо: True, т.к. объекты равны)")
    print(f"Хеш lock1 == Хеш lock3: {hash(lock1) == hash(lock3)} (Ожидаемо: False, т.к. объекты не равны)")

    # Тестирование использования в set (множестве)
    print("\n4. Тестирование в множестве (set):")
    lock_set = set()
    lock_set.add(lock1)
    lock_set.add(lock2)  # Добавление идентичного объекта - не должно увеличивать размер
    lock_set.add(lock3)
    lock_set.add(lock4)
    print(f"Множество LockInfo объектов: {lock_set}")
    print(
        f"Размер множества: {len(lock_set)} (Ожидаемо: 3, т.к. lock1 и lock2 - это один и тот же элемент с точки зрения хеша и равенства)")

    # Тестирование использования в dict (словаре)
    print("\n5. Тестирование в словаре (dict):")
    lock_dict = {}
    lock_dict[lock1] = "Это первый лок"
    lock_dict[lock2] = "Это второй лок (фактически, перезапишет первый, т.к. ключи равны)"
    lock_dict[lock3] = "Это третий лок"
    print(f"Словарь с LockInfo объектами в качестве ключей: {lock_dict}")
    print(f"Значение по lock1: {lock_dict[lock1]}")
    print(f"Значение по lock3: {lock_dict[lock3]}")

    print("\n--- Тестирование завершено ---")
