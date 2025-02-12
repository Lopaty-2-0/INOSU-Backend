import sqlalchemy as sql
from src.__init__ import db

class Specialization(db.Model):
    __tablename__ = "Specialization"

    id = sql.Column(sql.Integer, primary_key = True, autoincrement = True)
    name = sql.Column(sql.VARCHAR(45), unique = True, nullable = False)
    abbrevation = sql.Column(sql.CHAR(1), unique = True, nullable = False)
    lengthOfStudy = sql.Column(sql.Integer, nullable = False)

    def __init__(self, name, abbrevation, lengthOfStudy):
        self.name = name
        self.abbrevation = abbrevation
        self.lengthOfStudy = lengthOfStudy

    def __repr__(self):
        return f'<Team {self.name, self.abbrevation, self.lengthOfStudy!r}>'