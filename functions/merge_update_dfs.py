import pandas as pd


def merge_update_df(df_left,
                    df_right,
                    update_colname,
                    values_from_colname,
                    merge_on_colname):
    """
    Обновляет данные в df_left, объединяя его с df_right и конкатенируя строки.
    """
    print(f'Размерность левого ДФ составила: <{df_left.shape}>')
    print(f'Размерность правого ДФ составила: <{df_right.shape}>')

    # 1. Проверяем наличие нужных колонок в обоих DataFrames
    for col in [merge_on_colname, update_colname]:
        if col not in df_left.columns:
            raise ValueError(f"Колонка '{col}' отсутствует в левом DataFrame.")

    if merge_on_colname not in df_right.columns or values_from_colname not in df_right.columns:
        raise ValueError(f"Колонки '{merge_on_colname}' или '{values_from_colname}' отсутствуют в правом DataFrame.")

    # 2. Проверяем совпадение типов данных в ключах для соединения
    if df_left[merge_on_colname].dtype != df_right[merge_on_colname].dtype:
        raise TypeError(f"Типы данных в колонке '{merge_on_colname}' не совпадают между левым и правым DataFrame.")

    # Создаем копию левого DataFrame, чтобы избежать изменения оригинала
    df_merged = df_left.copy()

    # 3. Производим внешнее соединение (LEFT JOIN) по заданному ключу
    df_merged = pd.merge(df_merged, df_right[[merge_on_colname, values_from_colname]], on=merge_on_colname, how='left')

    # 4. Объединяем значения путем конкатенации строк
    df_merged[update_colname] = df_merged.apply(
        lambda row: f"{row[update_colname]}, {row[values_from_colname]}"
        if not pd.isna(row[values_from_colname]) else row[update_colname],
        axis=1
    )

    # 5. Удаляем временную колонку
    if values_from_colname in df_merged.columns:
        df_merged = df_merged.drop(columns=[values_from_colname])

    # Возвращаем обновленный DataFrame
    print(f'Размерность ИТОГОВОГО (смердженного) ДФ составила: <{df_merged.shape}>')
    return df_merged


# Тестируем функцию
if __name__ == "__main__":
    # Исходные данные
    data_left = {
        'id': [1, 2, 3],
        'name': ['Alice', 'Bob', 'Charlie'],
        'info': ['info1', 'info2', 'info3']
    }
    data_right = {
        'id': [2, 3, 4],
        'extra_info': ['extra2', 'extra3', 'extra4']
    }

    df_left = pd.DataFrame(data_left)
    df_right = pd.DataFrame(data_right)

    # Выполняем обновление info-колонки
    try:
        df_updated = merge_update_df(df_left, df_right, 'info', 'extra_info', 'id')
        print("Результат:\n", df_updated)

        # Тестируем ошибку при неверном имени колонки
        df_updated_fail = merge_update_df(df_left, df_right, 'info', 'wrong_col', 'id')
        print("Этот код не должен выполняться")

    except Exception as e:
        print("Ошибка:", str(e))

    # Тестируем конфликт типов данных
    try:
        df_right_wrong_type = df_right.copy()
        df_right_wrong_type['id'] = df_right_wrong_type['id'].astype(str)  # Меняем тип данных в колонке id
        df_updated_fail_type = merge_update_df(df_left, df_right_wrong_type, 'info', 'extra_info', 'id')

    except Exception as e:
        print("Ошибка:", str(e))
