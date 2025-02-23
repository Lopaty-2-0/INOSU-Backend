from app import db

class Team(db.Model):
    __tablename__ = "team"

    idUser = db.Column(db.Integer, db.ForeignKey("user.id"), primary_key = True)
    idTask = db.Column(db.Integer, db.ForeignKey("task.id"), primary_key = True)
    leader = db.Column(db.Boolean, nullable = False)

    def __init__(self, idUser, idTask, leader):
        self.idUser = idUser
        self.idTask = idTask
        self.leader = leader

    def __repr__(self):
        return f"<team {self.idTask, self.idUser, self.leader!r}>"