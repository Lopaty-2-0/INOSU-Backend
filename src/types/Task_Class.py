import sqlalchemy as sql
from src.database import Base

class Task_Class(Base):
    __tablename__ = "Task_Class"
    idTask = sql.Column(sql.Integer, sql.ForeignKey("Task.id"), primary_key = True)
    idClass = sql.Column(sql.Integer, sql.ForeignKey("Class.id"), primary_key = True)    
    
    def __init__(self, idTask, idClass):
        self.idTask = idTask
        self.idClass = idClass