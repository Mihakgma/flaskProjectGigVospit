import re

import pandas as pd


def phone_number_fix(phone):
    if phone:
        phone = re.sub(r'[^\d+]', '', str(phone))
        if phone.startswith("+7"):
            phone = phone.replace("+7", "8")
        return phone
    return None


def date_fix(date_str):
    if date_str:
        return pd.to_datetime(date_str, dayfirst=True, format="%d.%m.%Y", errors='coerce')
    return pd.NaT


def names_fix(name):
    if name:
        return name.strip().upper()
    return None


def elmk_snils_fix(value):
    if value:
        return re.sub(r'\D', '', str(value))
    return None
