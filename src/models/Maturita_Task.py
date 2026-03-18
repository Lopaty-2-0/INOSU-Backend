from app import db
from sqlalchemy.dialects.mysql import INTEGER

class Maturita_Task(db.Model):
    __tablename__ = "maturita_task"

    idTopic = db.Column(INTEGER(unsigned=True), db.ForeignKey("topic.id", ondelete = "CASCADE"), primary_key = True, nullable = False)
    idTask = db.Column(INTEGER(unsigned=True), primary_key = True, nullable = False)
    guarantor = db.Column(INTEGER(unsigned=True), primary_key = True, nullable = False)
    objector = db.Column(INTEGER(unsigned=True), nullable = True)
    idMaturita = db.Column(INTEGER(unsigned=True), db.ForeignKey("maturita.id", ondelete = "CASCADE"), primary_key = True, nullable = True)
    variant = db.Column(db.CHAR(1), nullable = True)

    __table_args__ = (
        db.ForeignKeyConstraint(
            ["idTask", "guarantor"],
            ["task.id", "task.guarantor"],
            ondelete = "CASCADE"
        ),
    )

    def __init__(self, idTopic, idTask, guarantor, objector, idMaturita, variant):
        self.idTopic = idTopic
        self.idTask = idTask
        self.objector = objector
        self.guarantor = guarantor
        self.idMaturita = idMaturita
        self.variant = variant

    def __repr__(self):
        return f"<maturita_task {self.idTask, self.idTopic, self.objector, self.guarantor, self.idMaturita, self.variant!r}>"