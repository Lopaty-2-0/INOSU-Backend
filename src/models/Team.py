from app import db
from src.utils.enums import Status
from sqlalchemy.dialects.mysql import TEXT, INTEGER, FLOAT

class Team(db.Model):
    __tablename__ = "team"

    idTeam = db.Column(INTEGER(unsigned=True), primary_key=True)
    idTask = db.Column(INTEGER(unsigned=True), db.ForeignKey("task.id"), primary_key=True)
    points = db.Column(FLOAT(unsigned=True), nullable=True)
    review = db.Column(TEXT, nullable=True)
    status = db.Column(db.Enum(Status), nullable=False)
    name = db.Column(db.String(255), nullable=True)

    def __init__(self, idTeam, idTask, name, review = None, status = None, points = None):
        self.idTeam = idTeam
        self.idTask = idTask
        self.points = points
        self.review = review
        self.status = status
        self.name = name

    def __repr__(self):
        return f"<team {self.idTeam, self.idTask, self.points, self.review, self.status, self.name!r}>"