from functions.parser_functs import (excel_to_data_frame_parser,
                                     unique_rows_with_max_columns,
                                     save_dataframe_to_json)

if __name__ == '__main__':
    file_path = "../Сведения о договорах ОГВиА оригинал!!!.xls"
    df = excel_to_data_frame_parser(file_path,
                                    "2025 ю.л.")
    print(df.shape)
    df = df.drop_duplicates()
    df["inn"] = df.inn.apply(lambda x: str(int(x)))
    df["additional_info"] = df.additional_info.apply(lambda x: str(x).strip())
    df["name"] = df.name.apply(lambda x: str(x).upper())
    print(df.shape)
    inn_unique = list(df.inn.unique())
    print(len(inn_unique))
    print(df.dtypes)
    df = unique_rows_with_max_columns(df=df,
                                      filter_upon_colname="inn",
                                      sort_by_colname="name")
    print(df.shape)
    print(df.name.value_counts().sort_values(ascending=False).head(10))
    print(df.name.head())
    print(df.name.tail())
    save_dataframe_to_json(df=df)
