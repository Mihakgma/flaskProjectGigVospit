import re

import numpy as np
import pandas as pd
import os
import json

from functions.data_fix import names_fix, phone_number_fix, elmk_snils_fix


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
    """Трансформация DataFrame заявителей с упрощенной логикой."""

    handlers = {
        'fio': kwargs.get("names_fix", names_fix),
        'phone': kwargs.get("phone_number_fix", phone_number_fix),
        'snils': kwargs.get("elmk_snils_fix", elmk_snils_fix),
    }

    df_out = pd.DataFrame(columns=columns_info.values())

    for index, row in df_in.iterrows():
        new_row = {}

        # Обработка ФИО
        last_name = handlers['fio'](row.get('фамилия'))
        first_name = handlers['fio'](row.get('имя'))
        middle_name = handlers['fio'](row.get('отчество'))

        if not last_name or not first_name:
            names = row.get(fio_colname, "").split()
            if names:
                last_name = last_name or handlers['fio'](names[0])
                if len(names) > 1:
                    first_name_part = names[1].split(".")[0] if "." in names[1] else names[1][
                        0]  # Извлекаем инициал имени
                    first_name = first_name or handlers['fio'](first_name_part)
                if len(names) > 2:
                    middle_name_part = names[2].split(".")[0] if "." in names[2] else names[2][
                        0]  # Извлекаем инициал отчества
                    middle_name = middle_name or handlers['fio'](middle_name_part)

        # Заполнение инициалов только если соответствующее полное поле пустое
        if last_name:
            if not first_name:
                new_row['first_name'] = 'И'
            if not middle_name:
                new_row['middle_name'] = 'О'

        new_row['last_name'] = last_name
        new_row['first_name'] = first_name
        new_row['middle_name'] = middle_name

        # Обработка остальных полей
        for in_col, out_col in columns_info.items():
            if out_col not in ('first_name', 'middle_name', 'last_name'):
                value = row.get(in_col)
                handler = handlers.get(out_col.split('_')[0] if '_' in out_col else in_col, lambda x: x)
                if out_col in ('medbook_number', 'passport_number', 'snils_number'):  # Обработка как для СНИЛС
                    handler = handlers['snils']
                new_row[out_col] = handler(value)

        df_out = pd.concat([df_out, pd.DataFrame([new_row])], ignore_index=True)

    # Замена пустых строк на NaN после цикла
    nullable_fields = ['middle_name',
                       'passport_number',
                       'registration_address',
                       'residence_address',
                       'phone_number',
                       'email',
                       'additional_info']
    df_out[nullable_fields] = df_out[nullable_fields].replace('', np.nan)

    return df_out
