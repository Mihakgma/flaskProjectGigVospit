from functions.default_db_data.parser_functs import (excel_to_data_frame_parser,
                                                     unique_rows_with_max_columns,
                                                     transform_applicants_data, save_dataframe_to_json)
from functions.data_fix import (phone_number_fix,
                                names_fix,
                                elmk_snils_fix)

applicants_colnames = {
    "имя": "first_name",
    "отчество": "middle_name",
    "фамилия": "last_name",
    "Номер ЭЛМК": "medbook_number",
    "СНИЛС": "snils_number",
    "паспорт_номер": "passport_number",
    "Дата рождения": "birth_date",
    "адрес_регистрации": "registration_address",
    "адрес_фактический": "residence_address",
    "номер_телефона": "phone_number",
    "е_майл": "email",
    "филиал": "additional_info"
}

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
    df_snils_unique = unique_rows_with_max_columns(df=df_elmk_unique,
                                                   filter_upon_colname="СНИЛС",
                                                   sort_by_colname="ФИО")
    print(df_snils_unique.shape)
    print(df_snils_unique.ФИО.head())
    df_applicants, df_vizits = transform_applicants_data(df_in=df_snils_unique,
                                                         fio_colname="ФИО",
                                                         first_name_colname="имя",
                                                         columns_info=applicants_colnames,
                                                         phone_number_fix=phone_number_fix,
                                                         date_in_colname="Дата поступления",
                                                         names_fix=names_fix,
                                                         elmk_snils_fix=elmk_snils_fix)
    save_dataframe_to_json(df=df_applicants, file_path='applicant.json')
    save_dataframe_to_json(df=df_vizits, file_path='vizit.json')
