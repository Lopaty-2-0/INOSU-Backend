from app import db

class Class(db.Model):
    __tablename__ = "Class"

    id = db.Column(db.Integer, primary_key = True, autoincrement = True)
    grade = db.Column(db.Integer, nullable = False)
    group = db.Column(db.CHAR(1), nullable = False)
    idSpecialization = db.Column(db.Integer, db.ForeignKey("Specialization.id"), nullable = False)

    def __init__(self, grade, group, idSpecialization):
        self.grade = grade
        self.group = group
        self.idSpecialization = idSpecialization

    def __repr__(self):
        return f'<Team {self.grade, self.group ,self.idSpecialization!r}>'