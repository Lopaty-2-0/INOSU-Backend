from app import db

class Team(db.Model):
    __tablename__ = "Team"

    idUser = db.Column(db.Integer, db.ForeignKey("User.id"), primary_key = True)
    idTask = db.Column(db.Integer, db.ForeignKey("Task.id"), primary_key = True)
    leader = db.Column(db.Boolean, nullable = False)

    def __init__(self, idUser, idTask, leader):
        self.idUser = idUser
        self.idTask = idTask
        self.leader = leader

    def __repr__(self):
        return f'<Team {self.idTask, self.idUser, self.leader!r}>'