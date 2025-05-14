from app import db

class User_Task(db.Model):
    __tablename__ = "user_task"

    idUser = db.Column(db.Integer, db.ForeignKey("user.id"), primary_key = True)
    idTask = db.Column(db.Integer, db.ForeignKey("task.id"), primary_key = True)
    elaboration = db.Column(db.VARCHAR(255))
    review = db.Column(db.VARCHAR(255))
    status = db.Column(db.VARCHAR(255), nullable = False) #pending, approved, rejected

    def __init__(self, idUser, idTask, elaboration, review, status):
        self.idUser = idUser
        self.idTask = idTask
        self.elaboration = elaboration
        self.review = review
        self.status = status

    def __repr__(self):
        return f"<team {self.idTask, self.idUser!r}>"