from app import db
from sqlalchemy.dialects.mysql import INTEGER

class User_Team(db.Model):
    __tablename__ = "user_team"
    
    idUser = db.Column(INTEGER(unsigned=True), db.ForeignKey("user.id"), primary_key = True)
    idTeam = db.Column(INTEGER(unsigned=True), db.ForeignKey("team.idTeam"), primary_key = True)    
    idTask = db.Column(INTEGER(unsigned=True), db.ForeignKey("task.id"), primary_key = True)

    def __init__(self, idUser, idTeam, idTask):
        self.idUser = idUser
        self.idTeam = idTeam
        self.idTask = idTask

    def __repr__(self):
        return f"<user_team {self.idUser, self.idTeam, self.idTask!r}>"