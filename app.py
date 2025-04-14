from flask import (Flask,
                   render_template,
                   jsonify,
                   request)
from flask_sqlalchemy import SQLAlchemy
import os

app = Flask(__name__)

# Путь к базе данных в корневой папке проекта
basedir = os.path.abspath(os.path.dirname(__file__))  # Получаем абсолютный путь к директории проекта
db_path = os.path.join(basedir, 'example.db')  # Формируем путь к файлу БД

app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{db_path}'  # Используем f-строку для подстановки пути
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False  # Добавлено для устранения предупреждения
db = SQLAlchemy(app)


# db.Query("CREATE TABLE users IF NOT EXISTS")


@app.route('/hello/<name>')
def hello(name):
    return render_template('hello.html', name=name)


@app.route('/data')
def data():
    return jsonify({'ключ': 'значение'})


@app.route('/submit', methods=['POST'])
def submit():
    name = request.form['name']
    return f'Введенные Вами данные: <{name}>'


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)

    def __repr__(self):
        return f'<User {self.username}>'


with app.app_context():
    db.create_all()


@app.route('/add_user', methods=['POST'])
def add_user():
    try:
        name = request.form['user_name']
        email = request.form['user_email']
        new_user = User(username=name, email=email)
        db.session.add(new_user)
        db.session.commit()
        db.session.close()
        return jsonify(new_user.__dict__)
    except Exception as e:  # Обработка ошибок
        db.session.rollback()  # Откатываем изменения в случае ошибки
        return jsonify({'error': str(e)}), 500


if __name__ == '__main__':
    app.run(debug=True)
