import datetime
from app import db
from src.utils.enums import Type

class Task(db.Model):
    __tablename__ = "task"

    id = db.Column(db.Integer, primary_key = True, autoincrement = True)
    name = db.Column(db.VARCHAR(45), nullable = False)
    startDate = db.Column(db.DateTime, default = datetime.datetime.now,nullable = False)
    endDate = db.Column(db.DateTime, nullable = False)
    task = db.Column(db.VARCHAR(255), nullable = False)
    guarantor = db.Column(db.Integer, db.ForeignKey("user.id"),nullable = False)
    type = db.Column(db.Enum(Type))

    def __init__(self, name, startDate, endDate, task, guarantor, type):
        self.name = name
        self.startDate = startDate
        self.endDate = endDate
        self.task = task
        self.guarantor = guarantor
        self.type = type

    def __repr__(self):
        return f"<task {self.name, self.startDate, self.endDate, self.task, self.guarantor, self.type!r}>"