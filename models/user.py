from database import db
from sqlalchemy import ForeignKey, event
# from .role import Role
# from .department import Department
# from .status import Status

user_roles = db.Table('user_roles',
                      db.Column('user_id', db.Integer, db.ForeignKey('user.id')),
                      db.Column('role_id', db.Integer, db.ForeignKey('role.id'))
                      )


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    last_name = db.Column(db.String(80), nullable=False)  # Фамилия
    first_name = db.Column(db.String(80), nullable=False)  # Имя
    middle_name = db.Column(db.String(80))  # Отчество
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(128), nullable=False)  # Пароль
    phone = db.Column(db.String(20))  # Телефон
    roles = db.relationship('Role', secondary=user_roles, backref=db.backref('users', lazy=True))
    dept_id = db.Column(db.Integer, ForeignKey('department.id'), nullable=False)  # ID отдела
    status_id = db.Column(db.Integer, ForeignKey('status.id'), nullable=False)  # ID статуса

    def __repr__(self):  # Исправлено на __repr__
        return f'<User {self.username}>'

    @property
    def dict(self):  # сериализация для JSON
        return {
            'id': self.id,
            'last_name': self.last_name,
            'first_name': self.first_name,
            'middle_name': self.middle_name,
            'username': self.username,
            'email': self.email,
            # 'password': self.password, # Пароль обычно не включают в сериализацию
            'phone': self.phone,
            'role_ids': self.roles,
            'dept_id': self.dept_id,
            'status_id': self.status_id
        }


@event.listens_for(User, 'mapper_configured')  # Или Role, 'after_mapper_configured'
def create_user_roles_table(mapper, class_):
    user_roles.create(db.engine, checkfirst=True)  # checkfirst - не создает, если уже существует
