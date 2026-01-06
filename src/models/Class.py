from app import db
from sqlalchemy.dialects.mysql import INTEGER

class Class(db.Model):
    __tablename__ = "class"

    id = db.Column(INTEGER(unsigned=True), primary_key=True, autoincrement=True)
    grade = db.Column(INTEGER(unsigned=True), nullable=False)
    group = db.Column(db.String(1), nullable=False)
    idSpecialization = db.Column(INTEGER(unsigned=True), db.ForeignKey("specialization.id"), nullable=False)
    name = db.Column(db.String(255), nullable=False, unique=True)

    def __init__(self, grade, group, idSpecialization, name):
        self.grade = grade
        self.group = group
        self.idSpecialization = idSpecialization
        self.name = name

    def __repr__(self):
        return f"<class {self.grade, self.group ,self.idSpecialization, self.name!r}>"