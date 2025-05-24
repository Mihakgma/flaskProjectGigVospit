import re

import pandas as pd


def phone_number_fix(phone):
    if phone is not None:
        phone = re.sub(r'[^\d+]', '', str(phone))
        if phone.startswith("+7"):
            phone = phone.replace("+7", "8")
        return phone
    return ""


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
        value = re.sub(r'\D', '', str(value))
        return value.replace("-", "")
    return None


def address_names_fix(name):
    if name:
        return name.strip().upper()
    return ""
