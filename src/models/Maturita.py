from app import db
from sqlalchemy.dialects.mysql import FLOAT, INTEGER, TIMESTAMP
import datetime

class Maturita(db.Model):
    __tablename__ = "maturita"

    id = db.Column(INTEGER(unsigned=True), primary_key = True, autoincrement = True)
    grade = db.Column(db.VARCHAR(9), unique = True, nullable = False)
    maxPoints = db.Column(FLOAT(unsigned=True), nullable = False)
    startDate = db.Column(TIMESTAMP(timezone = True), default=lambda:datetime.datetime.now(datetime.timezone.utc), nullable=False)
    endDate = db.Column(TIMESTAMP(timezone = True), default=lambda:datetime.datetime.now(datetime.timezone.utc), nullable=False)

    def __init__(self, grade, maxPoints, startDate, endDate):
        self.grade = grade
        self.maxPoints = maxPoints
        self.startDate = startDate
        self.endDate = endDate



    def __repr__(self):
        return f"<maturita {self.grade, self.maxPoints, self.startDate, self.endDate!r}>"