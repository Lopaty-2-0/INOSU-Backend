from app import db

class Task_Class(db.Model):
    __tablename__ = "task_class"
    idTask = db.Column(db.Integer, db.ForeignKey("task.id"), primary_key = True)
    idClass = db.Column(db.Integer, db.ForeignKey("class.id"), primary_key = True)    
    
    def __init__(self, idTask, idClass):
        self.idTask = idTask
        self.idClass = idClass

    def __repr__(self):
        return f"<task_class {self.idTask, self.idClass!r}>"