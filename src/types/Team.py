import sqlalchemy as sql
from src.database import Base

class Team(Base):
    __tablename__ = "Team"

    idUser = sql.Column(sql.Integer, sql.ForeignKey("User.id"), primary_key = True)
    idTask = sql.Column(sql.Integer, sql.ForeignKey("Task.id"), primary_key = True)
    leader = sql.Column(sql.Boolean, nullable = False)

    def __init__(self, idUser, idTask, leader):
        self.idUser = idUser
        self.idTask = idTask
        self.leader = leader