from app import db
from src.utils.enums import Status
from sqlalchemy.dialects.mysql import TEXT

class Team(db.Model):
    __tablename__ = "team"

    idTeam = db.Column(db.Integer, primary_key=True)
    idTask = db.Column(db.Integer, db.ForeignKey("task.id"), primary_key=True)
    points = db.Column(db.Integer, nullable=True)
    review = db.Column(TEXT, nullable=True)
    status = db.Column(db.Enum(Status), nullable=False)
    name = db.Column(db.String(255), nullable=True)

    def __init__(self, idTeam, idTask, review, status, points, name):
        self.idTeam = idTeam
        self.idTask = idTask
        self.points = points
        self.review = review
        self.status = status
        self.name = name

    def __repr__(self):
        return f"<team {self.idTeam, self.idTask, self.points, self.review, self.status, self.name!r}>"