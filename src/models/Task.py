import datetime
from app import db

class Task(db.Model):
    __tablename__ = "task"

    id = db.Column(db.Integer, primary_key = True, autoincrement = True)
    name = db.Column(db.VARCHAR(45), nullable = False)
    startDate = db.Column(db.DateTime, default = datetime.datetime.now,nullable = False)
    endDate = db.Column(db.DateTime, nullable = False)
    task = db.Column(db.VARCHAR(255), nullable = False)
    guarantor = db.Column(db.Integer, db.ForeignKey("user.id"),nullable = False)
    approve = db.Column(db.BOOLEAN, nullable = False)
    type = db.Column(db.Enum())

    def __init__(self, name, startDate, endDate, task, guarantor, approve):
        self.name = name
        self.startDate = startDate
        self.endDate = endDate
        self.task = task
        self.guarantor = guarantor
        self.approve = approve

    def __repr__(self):
        return f"<task {self.name, self.startDate, self.endDate, self.task, self.guarantor, self.approve!r}>"