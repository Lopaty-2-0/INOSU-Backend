import datetime
import sqlalchemy as sql
from src.database import Base

class User(Base):
    __tablename__ = "User"

    id = sql.Column(sql.Integer, primary_key = True, autoincrement=True)
    name = sql.Column(sql.VARCHAR(100), nullable = False)
    surname = sql.Column(sql.VARCHAR(100), nullable = False)
    abbreviation = sql.Column(sql.VARCHAR(4), unige = True)
    createdAt = sql.Column(sql.DateTime, default = datetime.datetime.now, nullable = False)
    role = sql.Column(sql.VARCHAR(45), nullable = False)
    password = sql.Column(sql.Text, nullable = False)
    profilePicture = sql.Column(sql.VARCHAR(255), default="/img/profile_photos/default.jpg", nullable=False)
    email = sql.Column(sql.VARCHAR(255), unique = True, nullable = False)
    idClass = sql.Column(sql.Integer, sql.ForeignKey("Class.id"))

    def __init__(self, name, surname, role, password, profilePicture, email, idClass = None, abbreviation = None):
        self.name = name
        self.surname = surname
        self.abbreviation = abbreviation
        self.role = role
        self.password = password
        self.profilePicture = profilePicture
        self.email = email
        self.idClass = idClass
