from app import db

class Task_Class(db.Model):
    __tablename__ = "Task_Class"
    idTask = db.Column(db.Integer, db.ForeignKey("Task.id"), primary_key = True)
    idClass = db.Column(db.Integer, db.ForeignKey("Class.id"), primary_key = True)    
    
    def __init__(self, idTask, idClass):
        self.idTask = idTask
        self.idClass = idClass

    def __repr__(self):
        return f'<Task_Class {self.idTask, self.idClass!r}>'