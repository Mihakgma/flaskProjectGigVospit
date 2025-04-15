from database import db


class Department(db.Model):  # Модель для Department
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)

    # ... другие поля, если нужны

    def __repr__(self):
        return f'<Department {self.name}>'
