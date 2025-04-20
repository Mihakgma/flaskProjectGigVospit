from pathlib import Path

db_path = Path(__file__).resolve().parent.parent / 'example.db'


class Config:
    SQLALCHEMY_DATABASE_URI = f'sqlite:///{db_path}'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
