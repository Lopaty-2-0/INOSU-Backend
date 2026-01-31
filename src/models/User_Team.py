from app import db
from sqlalchemy.dialects.mysql import INTEGER

class User_Team(db.Model):
    __tablename__ = "user_team"

    idUser = db.Column(INTEGER(unsigned=True), db.ForeignKey("user.id"), primary_key=True)
    idTeam = db.Column(INTEGER(unsigned=True), db.ForeignKey("team.idTeam"), primary_key=True)
    idTask = db.Column(INTEGER(unsigned=True), db.ForeignKey("team.idTask"), primary_key=True)
    guarantor = db.Column(INTEGER(unsigned=True), db.ForeignKey("team.guarantor"), primary_key=True)

    def __init__(self, idUser, idTeam, idTask, guarantor):
        self.idUser = idUser
        self.idTeam = idTeam
        self.idTask = idTask
        self.guarantor = guarantor

    def __repr__(self):
        return f"<user_team ({self.idUser}, {self.idTeam}, {self.idTask})>"