import datetime
from app import db

class User(db.Model):
    __tablename__ = "user"

    id = db.Column(db.Integer, primary_key = True, autoincrement=True)
    name = db.Column(db.VARCHAR(100), nullable = False)
    surname = db.Column(db.VARCHAR(100), nullable = False)
    abbreviation = db.Column(db.VARCHAR(4), unique = True)
    createdAt = db.Column(db.DateTime, default = datetime.datetime.now, nullable = False)
    role = db.Column(db.VARCHAR(45), nullable = False)
    password = db.Column(db.Text, nullable = False)
    profilePicture = db.Column(db.VARCHAR(255), server_default="/img/profile_photos/default.jpg")
    email = db.Column(db.VARCHAR(255), unique = True, nullable = False)
    idClass = db.Column(db.Integer, db.ForeignKey("class.id"), nullable = True)

    def __init__(self, name, surname, role, password, profilePicture, email, idClass = None, abbreviation = None):
        self.name = name
        self.surname = surname
        self.abbreviation = abbreviation
        self.role = role
        self.password = password
        self.profilePicture = profilePicture
        self.email = email
        self.idClass = idClass

    def __repr__(self):
        return f'<user {self.name, self.surname, self.role, self.email, self.idClass!r}>'