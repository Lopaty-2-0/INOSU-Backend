from app import db

class Team(db.Model):
    __tablename__ = "team"
    idTeam = db.Column(db.Integer, primary_key = True)
    idTask = db.Column(db.Integer, db.ForeignKey("task.id"), primary_key = True)
    elaboration = db.Column(db.VARCHAR(255))
    review = db.Column(db.VARCHAR(255))
    #udělat na enum
    status = db.Column(db.VARCHAR(255), nullable = False) #pending, approved, rejected
    
    def __init__(self, idTeam, idTask, elaboration, review, status):
        self.idTeam = idTeam
        self.idTask = idTask
        self.elaboration = elaboration
        self.review = review
        self.status = status

    def __repr__(self):
        return f"<task_class {self.idTeam, self.idTask!r}>"