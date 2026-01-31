from app import db
from sqlalchemy.dialects.mysql import INTEGER
import datetime

class Version_Team(db.Model):
    __tablename__ = "version_team"

    idVersion = db.Column(INTEGER(unsigned=True), primary_key=True)
    idTeam = db.Column(INTEGER(unsigned=True), db.ForeignKey("team.idTeam"), primary_key=True)
    idTask = db.Column(INTEGER(unsigned=True), db.ForeignKey("team.idTask"), primary_key=True)
    guarantor = db.Column(INTEGER(unsigned=True), db.ForeignKey("team.guarantor"), primary_key=True, nullable = False)
    elaboration = db.Column(db.String(255), nullable=True)
    createdAt = db.Column(db.DateTime(timezone=True), default=lambda:datetime.datetime.now(datetime.timezone.utc), nullable=False)

    def __init__(self, idTeam, idTask, elaboration, idVersion, guarantor):
        self.idTeam = idTeam
        self.idTask = idTask
        self.idVersion = idVersion
        self.elaboration = elaboration
        self.guarantor = guarantor

    def __repr__(self):
        return f"<version_team {self.idTeam, self.idTask, self.idVersion, self.elaboration!r}>"