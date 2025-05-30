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


