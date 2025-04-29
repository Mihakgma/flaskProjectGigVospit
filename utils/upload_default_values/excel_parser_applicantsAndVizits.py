from functions.parser_functs import (excel_to_data_frame_parser,
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
    # print(df_snils_unique.ФИО.tail(35))
    print(df_snils_unique.ФИО.head())
    df_transformed_applicants = transform_applicants_data(df_in=df_snils_unique,
                                                          fio_colname="ФИО",
                                                          columns_info=applicants_colnames,
                                                          phone_number_fix=phone_number_fix,
                                                          # date_fix=date_fix,
                                                          names_fix=names_fix,
                                                          elmk_snils_fix=elmk_snils_fix)
    # print(df_transformed_applicants.head())
    save_dataframe_to_json(df=df_transformed_applicants)
