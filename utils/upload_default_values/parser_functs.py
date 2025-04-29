import pandas as pd
import os
import json


def excel_to_data_frame_parser(file: str,
                               ws_name: str,
                               skip_cols: int = 0,
                               del_rows_after_parsing: int = 0,
                               parse_rows: int = 0,
                               parse_cols: int = 0,
                               **kwargs):
    """
    Парсит эксель-файл с выбором листа.
    Возвращает датафрейм.
    """
    if "~$" in file:
        return None

    try:
        file = file
    except BaseException as e:
        print(f"Ошибка ввода: {e}")
        return None

    data = pd.ExcelFile(file)
    ws_sheet_names = data.sheet_names
    print("Названия листов в книге:")
    print(ws_sheet_names)

    if ws_name in ws_sheet_names:
        print(f"Лист с именем <{ws_name}> найден в книге.")
    else:
        print(f"Лист с именем <{ws_name}> не найден в книге!")
        return None

    df = data.parse(sheet_name=ws_name, **kwargs)

    if skip_cols > 0:
        df = df.iloc[:, skip_cols:]
        df = df.reset_index(drop=True)

    if parse_rows > 0:
        df = df.iloc[:parse_rows, :]  # Берем строки от 0 до parse_rows (исключая parse_rows)
        df = df.reset_index(drop=True)

    if parse_cols > 0:
        df = df.iloc[:, :parse_cols]  # Берем столбцы от 0 до parse_cols (исключая parse_cols)
        df = df.reset_index(drop=True)

    if del_rows_after_parsing > 0:
        df = df.iloc[del_rows_after_parsing:, :]
        df = df.reset_index(drop=True)

    df = df.fillna(0)

    print(f'Размерность ДФ: <{df.shape}>')
    print('OK!')
    return df


def unique_rows_with_max_columns(df,
                                 filter_upon_colname,
                                 sort_by_colname):
    # Оставляем уникальные значения по указанной колонке
    filtered_df = df.drop_duplicates(subset=filter_upon_colname, keep=False)
    filtered_df.reset_index(drop=True, inplace=True)

    # Создаем новую колонку 'num_filled', содержащую число непустых значений в каждой строке
    filtered_df['num_filled'] = filtered_df.count(axis=1)

    # Сортируем сначала по количеству заполненных колонок (убывание),
    # потом — по указанному столбцу сортировки (возрастание)
    sorted_df = filtered_df.sort_values(by=['num_filled', sort_by_colname], ascending=[False, True])

    # Удаляем временную колонку num_filled перед возвратом результата
    return sorted_df.drop(columns='num_filled')


def save_dataframe_to_json(df, file_path=None):
    """
    Сохраняет пандас DataFrame в файл JSON с указанными особенностями структуры.

    :param df:
    Пандас DataFrame, который нужно сохранить.
    :param file_path:
    Полный путь к файлу, куда сохранить JSON (по умолчанию - текущая директория + имя файла 'output.json').
    """
    if not isinstance(df, pd.DataFrame):
        raise ValueError("Параметр df должен быть объектом типа pandas.DataFrame.")

    # Если путь не указан, используем текущую директорию
    if file_path is None:
        file_path = os.path.join(os.getcwd(), 'output.json')

    # Преобразуем индекс в строку начиная с единицы
    result_dict = {str(i + 1): row.to_dict() for i, (_, row) in enumerate(df.iterrows())}

    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(result_dict, f, ensure_ascii=False, indent=4)

    print(f"Данные успешно сохранены в файл '{file_path}'")
