from database import db
from sqlalchemy import Text


class Role(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)
    description = db.Column(Text)

    def __repr__(self):
        return f'<Role {self.name}>'
