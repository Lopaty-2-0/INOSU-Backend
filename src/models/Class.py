from app import db

class Class(db.Model):
    __tablename__ = "class"

    id = db.Column(db.Integer, primary_key = True, autoincrement = True)
    grade = db.Column(db.Integer, nullable = False)
    group = db.Column(db.CHAR(1), nullable = False)
    idSpecialization = db.Column(db.Integer, db.ForeignKey("specialization.id"), nullable = False)
    name = db.Column(db.VARCHAR(255), nullable = False, unique=True)

    def __init__(self, grade, group, idSpecialization, name):
        self.grade = grade
        self.group = group
        self.idSpecialization = idSpecialization
        self.name = name

    def __repr__(self):
        return f"<class {self.grade, self.group ,self.idSpecialization, self.name!r}>"