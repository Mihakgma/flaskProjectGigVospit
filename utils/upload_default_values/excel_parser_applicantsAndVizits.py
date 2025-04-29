from utils.upload_default_values.parser_functs import (excel_to_data_frame_parser,
                                                       unique_rows_with_max_columns)

if __name__ == '__main__':
    file_path = "../../ВСЕ_ВЫГРУЖЕННЫЕ_ЗАЯВЛЕНИЯ_ЭЛМК_03_02_2025_09_31.xlsx"
    df = excel_to_data_frame_parser(file_path,
                                    "Sheet1")
    print(df.shape)
    df = df.drop_duplicates()
    print(df.shape)
    df_elmk_unique = unique_rows_with_max_columns(df=df,
                                      filter_upon_colname="Номер ЭЛМК",
                                      sort_by_colname="Дата поступления")
    print(df_elmk_unique.shape)
    df_snils_unique = unique_rows_with_max_columns(df=df,
                                                  filter_upon_colname="СНИЛС",
                                                  sort_by_colname="Дата поступления")
    print(df_snils_unique.shape)
    print(df_snils_unique.head())