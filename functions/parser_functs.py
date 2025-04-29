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
    filtered_df = df.drop_duplicates(subset=filter_upon_colname, keep=False).copy()
    filtered_df.reset_index(drop=True, inplace=True)
    try:
        filtered_df.drop(columns='index', inplace=True)
    except BaseException as e:
        print(e, '\nprobably index column has been dropped before...')

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


def transform_applicants_data(df_in: pd.DataFrame,
                              fio_colname: str,
                              columns_info: dict,
                              *args,
                              **kwargs) -> pd.DataFrame:
    """
    Трансформирует DataFrame заявителей, извлекая и обрабатывая данные ФИО,
    номера телефонов, даты и другие поля.

    Args:
        df_in: Исходный DataFrame.
        fio_colname: Название столбца с ФИО.
        columns_info: Словарь соответствия названий столбцов.
        *args: Дополнительные функции обработки (phone_number_fix, date_fix, names_fix, elmk_snils_fix).
        **kwargs: Дополнительные аргументы для функций обработки.

    Returns:
        Трансформированный DataFrame.
    """

    df_out = pd.DataFrame(columns=columns_info.values())

    phone_number_fix = kwargs.get("phone_number_fix", lambda x: x)
    date_fix = kwargs.get("date_fix", lambda x: x)
    names_fix = kwargs.get("names_fix", lambda x: x)
    elmk_snils_fix = kwargs.get("elmk_snils_fix", lambda x: x)

    for index, row in df_in.iterrows():
        new_row = {}
        for in_col, out_col in columns_info.items():
            if out_col in ('first_name', 'middle_name', 'last_name'):  # Имя, Отчество, Фамилия
                names = row.get(fio_colname).split()
                if len(names) > 1:
                    last_name = names[0] if len(names) > 0 else None
                    first_name = names[1] if len(names) > 1 else None
                    middle_name = names[2] if len(names) > 2 else None
                new_row['first_name'] = names_fix(first_name) if first_name is not None else first_name
                new_row['middle_name'] = names_fix(middle_name) if middle_name is not None else middle_name
                new_row['last_name'] = names_fix(last_name) if last_name is not None else last_name

            elif out_col == 'phone_number':  # Телефон
                new_row[out_col] = phone_number_fix(row.get(in_col))

            elif out_col == 'birth_date':  # Дата рождения
                # new_row[out_col] = date_fix(row.get(in_col))
                new_row[out_col] = row.get(in_col)

            elif out_col in ('medbook_number', 'snils_number'):
                new_row[out_col] = elmk_snils_fix(row.get(in_col))
            elif out_col == 'additional_info':
                new_row[out_col] = row.get(in_col)

            else:  # Все остальные поля
                new_row[out_col] = row.get(in_col)

        df_out = pd.concat([df_out, pd.DataFrame([new_row])], ignore_index=True)

    return df_out
