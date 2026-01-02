from app import db
from sqlalchemy.dialects.mysql import INTEGER

class Version_Team(db.Model):
    __tablename__ = "version_team"

    idVersion = db.Column(INTEGER(unsigned=True), primary_key=True)
    idTeam = db.Column(INTEGER(unsigned=True), primary_key=True)
    idTask = db.Column(INTEGER(unsigned=True), primary_key=True)
    elaboration = db.Column(db.String(255), nullable=True)
    createdAt = db.Column(db.DateTime, default=None, nullable=True)

    __table_args__ = (
        db.ForeignKeyConstraint(
            ["idTeam", "idTask"],
            ["team.idTeam", "team.idTask"]
        ),
    )

    def __init__(self, idTeam, idTask, elaboration, idVersion):
        self.idTeam = idTeam
        self.idTask = idTask
        self.idVersion = idVersion
        self.elaboration = elaboration

    def __repr__(self):
        return f"<version_team {self.idTeam, self.idTask, self.idVersion, self.elaboration!r}>"