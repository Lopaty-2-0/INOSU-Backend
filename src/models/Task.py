import datetime
from app import db
from src.utils.enums import Type
from sqlalchemy.dialects.mysql import INTEGER, FLOAT

class Task(db.Model):
    __tablename__ = "task"

    id = db.Column(INTEGER(unsigned=True), primary_key = True, autoincrement = True)
    name = db.Column(db.VARCHAR(45), nullable = False)
    startDate = db.Column(db.DateTime, default = datetime.datetime.now, nullable = False)
    endDate = db.Column(db.DateTime, nullable = False)
    deadline = db.Column(db.DateTime, nullable = True)
    task = db.Column(db.VARCHAR(255), nullable = False)
    guarantor = db.Column(INTEGER(unsigned=True), db.ForeignKey("user.id"), nullable = False)
    type = db.Column(db.Enum(Type), nullable = False)
    points = db.Column(FLOAT(unsigned=True), nullable = True)

    def __init__(self, name, startDate, endDate, task, guarantor, type, points, deadline):
        self.name = name
        self.startDate = startDate
        self.endDate = endDate
        self.task = task
        self.guarantor = guarantor
        self.type = type
        self.points = points
        self.deadline = deadline

    def __repr__(self):
        return f"<task {self.name, self.startDate, self.endDate, self.task, self.guarantor, self.type, self.points, self.deadline!r}>"