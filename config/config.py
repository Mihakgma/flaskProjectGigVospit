# from pathlib import Path
#
# db_path = Path(__file__).resolve().parent.parent / 'example.db'

with open('config/db_conf_pg.txt', 'r') as file:
    db_config_info = file.read().replace('\n', '')


class Config:
    # SQLALCHEMY_DATABASE_URI = f'sqlite:///{db_path}'
    SQLALCHEMY_DATABASE_URI = "postgresql+psycopg2://postgres:Ex-machina6891@localhost:5432/gig_vospit"
    DATABASE_URL = "postgresql+psycopg2://postgres:Ex-machina6891@localhost:5432/gig_vospit"
    SQLALCHEMY_TRACK_MODIFICATIONS = False
