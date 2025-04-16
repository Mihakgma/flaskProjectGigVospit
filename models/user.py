# from database import db
# from sqlalchemy import ForeignKey, event, Text
#
# from .applicant import applicant_contract
#
#
# class Role(db.Model):
#     id = db.Column(db.Integer, primary_key=True)
#     name = db.Column(db.String(50), nullable=False)
#     description = db.Column(Text)
#
#     def __repr__(self):
#         return f'<Role {self.name}>'
#
#
# class Status(db.Model):
#     id = db.Column(db.Integer, primary_key=True)
#     name = db.Column(db.String(50), nullable=False)
#     description = db.Column(Text)
#
#     def __repr__(self):
#         return f'<Status {self.name}>'
#
#
# class Department(db.Model):  # Модель для Department
#     id = db.Column(db.Integer, primary_key=True)
#     name = db.Column(db.String(100), nullable=False)
#
#     # ... другие поля, если нужны
#
#     def __repr__(self):
#         return f'<Department {self.name}>'
#
#
# user_roles = db.Table('user_roles',
#                       db.Column('user_id', db.Integer, db.ForeignKey('user.id')),
#                       db.Column('role_id', db.Integer, db.ForeignKey('role.id'))
#                       )
#
#
# class User(db.Model):
#     id = db.Column(db.Integer, primary_key=True)
#     last_name = db.Column(db.String(80), nullable=False)  # Фамилия
#     first_name = db.Column(db.String(80), nullable=False)  # Имя
#     middle_name = db.Column(db.String(80))  # Отчество
#     username = db.Column(db.String(80), unique=True, nullable=False)
#     email = db.Column(db.String(120), unique=True, nullable=False)
#     password = db.Column(db.String(128), nullable=False)  # Пароль
#     phone = db.Column(db.String(20))  # Телефон
#     # roles = db.relationship('Role', secondary=user_roles, backref=db.backref('users', lazy=True))
#     dept_id = db.Column(db.Integer, ForeignKey('department.id'), nullable=False)  # ID отдела
#     status_id = db.Column(db.Integer, ForeignKey('status.id'), nullable=False)  # ID статуса
#
#     def __repr__(self):  # Исправлено на __repr__
#         return f'<User {self.username}>'
#
#     @property
#     def dict(self):  # сериализация для JSON
#         return {
#             'id': self.id,
#             'last_name': self.last_name,
#             'first_name': self.first_name,
#             'middle_name': self.middle_name,
#             'username': self.username,
#             'email': self.email,
#             # 'password': self.password, # Пароль обычно не включают в сериализацию
#             'phone': self.phone,
#             'role_ids': self.roles,
#             'dept_id': self.dept_id,
#             'status_id': self.status_id
#         }
#
#
# User.roles = db.relationship('Role', secondary=user_roles, backref=db.backref('users', lazy=True))
#
#
# @event.listens_for(db.metadata, 'mapper_configured')  # Используйте db.metadata
# def create_tables(mapper, class_):
#     if not user_roles.exists():
#         user_roles.create(db.get_engine())  # используйте db.get_engine()
#     if not applicant_contract.exists():
#         applicant_contract.create(db.get_engine())
