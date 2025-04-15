import os

basedir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))  # UP-LEVEL FROM CURRENT DIR!!!
# db_path = os.path.join(basedir, 'example.db')


class Config:
    # my favourite password...
    SECRET_KEY = os.environ.get('SECRET_KEY')
    # set DATABASE_URL="postgresql://user:password@localhost:5432/example"
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
