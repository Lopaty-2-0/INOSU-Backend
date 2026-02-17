from app import db
from sqlalchemy.dialects.mysql import INTEGER

class Conversation(db.Model):
    __tablename__ = "conversation"

    idConversation = db.Column(INTEGER(unsigned=True), primary_key=True, autoincrement=True)
    idUser1 = db.Column(INTEGER(unsigned=True), db.ForeignKey("user.id"), nullable = True)
    idUser2 = db.Column(INTEGER(unsigned=True), db.ForeignKey("user.id"), nullable = True)
    idTask = db.Column(INTEGER(unsigned=True), nullable = True)
    guarantor = db.Column(INTEGER(unsigned=True), nullable = True)
    isArchived = db.Column(db.Boolean, default=False, nullable=False)


    __table_args__ = (
        db.ForeignKeyConstraint(
            ["idTask", "guarantor"],
            ["task.id", "task.guarantor"],
            ondelete = "CASCADE"
        ),
    )

    def __init__(self, idUser1, idUser2, idTask, guarantor, isArchived):
        self.idUser1 = idUser1
        self.idUser2 = idUser2
        self.isArchived = isArchived
        self.idTask = idTask
        self.guarantor = guarantor

    def __repr__(self):
        return f"<conversation ({self.idUser1}, {self.idUser2}, {self.guarantor}, {self.idTask}, {self.isArchived})>"