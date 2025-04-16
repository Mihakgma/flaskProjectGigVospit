from flask import Blueprint, render_template, jsonify, request
from models.models import User  # Импортируем модель User
from database import db  # Импортируем db

routes_bp = Blueprint('routes', __name__)  # Создаем blueprint


@routes_bp.route('/hello/<name>')
def hello(name):
    return render_template('hello.html', name=name)


@routes_bp.route('/data')
def data():
    return jsonify({'ключ': 'значение'})


@routes_bp.route('/submit', methods=['POST'])
def submit():
    name = request.form['name']
    return f'Введенные Вами данные: <{name}>'


@routes_bp.route('/add_user', methods=['POST'])
def add_user():
    try:
        name = request.form['user_name']
        email = request.form['user_email']
        new_user = User(username=name, email=email)
        db.session.add(new_user)
        db.session.commit()
        return jsonify(new_user.dict), 201  # Код 201 Created
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500
