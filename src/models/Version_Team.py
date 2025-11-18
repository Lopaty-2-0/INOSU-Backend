from app import db

class Version_Team(db.Model):
    __tablename__ = "version_team"

    idTeam = db.Column(db.Integer, db.ForeignKey("team.idTeam"), primary_key=True)
    idVersion = db.Column(db.Integer, primary_key=True)
    idTask = db.Column(db.Integer, db.ForeignKey("task.id"), primary_key=True)
    elaboration = db.Column(db.String(255), nullable=True)

    def __init__(self, idTeam, idTask, elaboration, idVersion):
        self.idTeam = idTeam
        self.idTask = idTask
        self.idVersion = idVersion
        self.elaboration = elaboration

    def __repr__(self):
        return f"<version_team {self.idTeam, self.idTask, self.idVersion, self.elaboration!r}>"