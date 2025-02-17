from app import db

class Specialization(db.Model):
    __tablename__ = "Specialization"

    id = db.Column(db.Integer, primary_key = True, autoincrement = True)
    name = db.Column(db.VARCHAR(45), unique = True, nullable = False)
    abbrevation = db.Column(db.CHAR(1), unique = True, nullable = False)
    lengthOfStudy = db.Column(db.Integer, nullable = False)

    def __init__(self, name, abbrevation, lengthOfStudy):
        self.name = name
        self.abbrevation = abbrevation
        self.lengthOfStudy = lengthOfStudy

    def __repr__(self):
        return f'<Team {self.name, self.abbrevation, self.lengthOfStudy!r}>'