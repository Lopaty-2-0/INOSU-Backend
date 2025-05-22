from app import db

class Specialization(db.Model):
    __tablename__ = "specialization"

    id = db.Column(db.Integer, primary_key = True, autoincrement = True)
    name = db.Column(db.VARCHAR(45), unique = True, nullable = False)
    abbreviation = db.Column(db.CHAR(1), unique = True, nullable = False)
    lengthOfStudy = db.Column(db.Integer, nullable = False)

    def __init__(self, name, abbreviation, lengthOfStudy):
        self.name = name
        self.abbreviation = abbreviation
        self.lengthOfStudy = lengthOfStudy

    def __repr__(self):
        return f"<specialization {self.name, self.abbreviation, self.lengthOfStudy!r}>"