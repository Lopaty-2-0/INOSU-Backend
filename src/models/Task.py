import datetime
import sqlalchemy as sql
from src.__init__ import db

class Task(db.Model):
    __tablename__ = "Task"

    id = sql.Column(sql.Integer, primary_key = True, autoincrement = True)
    name = sql.Column(sql.VARCHAR(45), nullable = False)
    startDate = sql.Column(sql.DateTime, default = datetime.datetime.now,nullable = False)
    endDate = sql.Column(sql.DateTime, nullable = False)
    task = sql.Column(sql.VARCHAR(255), nullable = False)
    elaboration = sql.Column(sql.VARCHAR(255), nullable = False)
    review = sql.Column(sql.VARCHAR(255), nullable = False)
    guarantor = sql.Column(sql.Integer, sql.ForeignKey("User.id"),nullable = False)

    def __init__(self, name, startDate, endDate, task, elaboration, review, guarantor):
        self.name = name
        self.startDate = startDate
        self.endDate = endDate
        self.task = task
        self.elaboration = elaboration
        self.review = review
        self.guarantor = guarantor

    def __repr__(self):
        return f'<Task {self.name, self.startDate, self.endDate, self.task, self.guarantor!r}>'