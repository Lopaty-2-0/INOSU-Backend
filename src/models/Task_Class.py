import sqlalchemy as sql
from src.__init__ import db

class Task_Class(db.Model):
    __tablename__ = "Task_Class"
    idTask = sql.Column(sql.Integer, sql.ForeignKey("Task.id"), primary_key = True)
    idClass = sql.Column(sql.Integer, sql.ForeignKey("Class.id"), primary_key = True)    
    
    def __init__(self, idTask, idClass):
        self.idTask = idTask
        self.idClass = idClass

    def __repr__(self):
        return f'<Task_Class {self.idTask, self.idClass!r}>'