import sqlalchemy as sql
from src.database import Base

class Class(Base):
    __tablename__ = "Class"

    id = sql.Column(sql.Integer, primary_key = True, autoincrement = True)
    grade = sql.Column(sql.Integer, nullable = False)
    group = sql.Column(sql.CHAR(1), nullable = False)
    idSpecialization = sql.Column(sql.Integer, sql.ForeignKey("Specialization.id"), nullable = False)

    def __init__(self, grade, group):
        self.grade = grade
        self.group = group