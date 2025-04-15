import os

basedir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))  # UP-LEVEL FROM CURRENT DIR!!!
db_path = os.path.join(basedir, 'example.db')


class Config:
    SQLALCHEMY_DATABASE_URI = f'sqlite:///{db_path}'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
