import sqlalchemy as sql
from src.__init__ import db

class Class(db.Model):
    __tablename__ = "Class"

    id = sql.Column(sql.Integer, primary_key = True, autoincrement = True)
    grade = sql.Column(sql.Integer, nullable = False)
    group = sql.Column(sql.CHAR(1), nullable = False)
    idSpecialization = sql.Column(sql.Integer, sql.ForeignKey("Specialization.id"), nullable = False)

    def __init__(self, grade, group, idSpecialization):
        self.grade = grade
        self.group = group
        self.idSpecialization = idSpecialization

    def __repr__(self):
        return f'<Team {self.grade, self.group ,self.idSpecialization!r}>'