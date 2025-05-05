# from pathlib import Path
#
# db_path = Path(__file__).resolve().parent.parent / 'example.db'

with open('config/db_conf_pg.txt', 'r') as file:
    db_config_info = file.read().replace('\n', '')

class Config:
    # SQLALCHEMY_DATABASE_URI = f'sqlite:///{db_path}'
    SQLALCHEMY_DATABASE_URI = db_config_info
    SQLALCHEMY_TRACK_MODIFICATIONS = False
