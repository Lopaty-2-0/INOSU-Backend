import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
from app import db
from src.utils.enums import Role

class User(db.Model, UserMixin):
    __tablename__ = "user"

    id = db.Column(db.Integer, primary_key = True, autoincrement=True)
    name = db.Column(db.VARCHAR(100), nullable = False)
    surname = db.Column(db.VARCHAR(100), nullable = False)
    abbreviation = db.Column(db.VARCHAR(4), unique = True)
    createdAt = db.Column(db.DateTime, default = datetime.datetime.now, nullable = False)
    role = db.Column(db.Enum(Role), nullable = False)
    password = db.Column(db.Text, nullable = False)
    profilePicture = db.Column(db.VARCHAR(255), server_default="default.jpg")
    email = db.Column(db.VARCHAR(255), unique = True, nullable = False)
    updatedAt = db.Column(db.DateTime, default = datetime.datetime.now, nullable = False)

    @property
    def hash_password(self):
        raise AttributeError("password not readable")
    
    @hash_password.setter
    def hashed_password(self, password):
        self.password = generate_password_hash(password)

    def verify_password(self, password):
        return check_password_hash(self.password, password)

    def __init__(self, name, surname, role, password, profilePicture, email, abbreviation = None):
        self.name = name
        self.surname = surname
        self.abbreviation = abbreviation
        self.role = role
        self.password = password
        self.profilePicture = profilePicture
        self.email = email
    
    def __repr__(self):
        return f"<user {self.name, self.surname, self.role, self.email!r}>"