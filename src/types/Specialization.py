import sqlalchemy as sql
from src.database import Base

class Specialization(Base):
    __tablename__ = "Specialization"

    id = sql.Column(sql.Integer, primary_key = True, autoincrement = True)
    name = sql.Column(sql.VARCHAR(45), unique = True, nullable = False)
    abbrevation = sql.Column(sql.CHAR(1), unique = True, nullable = False)
    lengthOfStudy = sql.Column(sql.Integer, nullable = False)

    def __init__(self, name, abbrevation, lengthOfStudy):
        self.name = name
        self.abbrevation = abbrevation
        self.lengthOfStudy = lengthOfStudy
