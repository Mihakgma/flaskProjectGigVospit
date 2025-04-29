import re

import pandas as pd


def phone_number_fix(phone):
    if phone:
        return re.sub(r'[^\d+]', '', str(phone))
    return None


def date_fix(date_str):
    if date_str:
        return pd.to_datetime(date_str, dayfirst=True, format="%d.%m.%Y", errors='coerce')
    return pd.NaT


def names_fix(name):
    if name:
        return name.strip().capitalize()
    return None


def elmk_snils_fix(value):
    if value:
        return re.sub(r'[^\d]', '', str(value))
    return None
