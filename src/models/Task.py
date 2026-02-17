import datetime
from app import db
from src.utils.enums import Type
from sqlalchemy.dialects.mysql import INTEGER, FLOAT

class Task(db.Model):
    __tablename__ = "task"

    id = db.Column(INTEGER(unsigned=True), primary_key = True)
    name = db.Column(db.VARCHAR(255), nullable = False)
    startDate = db.Column(db.DateTime(timezone = True), default=lambda:datetime.datetime.now(datetime.timezone.utc), nullable = False)
    endDate = db.Column(db.DateTime(timezone = True), nullable = False)
    deadline = db.Column(db.DateTime(timezone = True), nullable = True)
    task = db.Column(db.VARCHAR(255), nullable = True)
    guarantor = db.Column(INTEGER(unsigned=True), db.ForeignKey("user.id", ondelete = "CASCADE"), primary_key = True, nullable = False)
    type = db.Column(db.Enum(Type), nullable = False)
    points = db.Column(FLOAT(unsigned=True), nullable = True)

    def __init__(self, name, startDate, endDate, task, guarantor, type, points, deadline, id):
        self.name = name
        self.startDate = startDate
        self.endDate = endDate
        self.task = task
        self.guarantor = guarantor
        self.type = type
        self.points = points
        self.deadline = deadline
        self.id = id

    def __repr__(self):
        return f"<task {self.name, self.startDate, self.endDate, self.task, self.guarantor, self.type, self.points, self.deadline!r}>"