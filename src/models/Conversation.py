from app import db
from sqlalchemy.dialects.mysql import INTEGER

class Conversation(db.Model):
    __tablename__ = "conversation"

    idConversation = db.Column(INTEGER(unsigned=True), primary_key=True)
    idUser1 = db.Column(INTEGER(unsigned=True), db.ForeignKey("user.id"), primary_key=True)
    idUser2 = db.Column(INTEGER(unsigned=True), db.ForeignKey("user.id"), primary_key=True)
    idTask = db.Column(INTEGER(unsigned=True), nullable = True)
    guarantor = db.Column(INTEGER(unsigned=True), nullable = True)
    isArchived = db.Column(db.Boolean, default=False, nullable=False)
    deletedUser1 = db.Column(db.Boolean, default=False, nullable=False)
    deletedUser2 = db.Column(db.Boolean, default=False, nullable=False)


    __table_args__ = (
        db.ForeignKeyConstraint(
            ["idTask", "guarantor"],
            ["task.id", "task.guarantor"],
            ondelete = "CASCADE"
        ),
    )

    def __init__(self, idConversation, idUser1, idUser2, idTask, guarantor, isArchived, deletedUser1, deletedUser2):
        self.idConversation = idConversation
        self.idUser1 = idUser1
        self.idUser2 = idUser2
        self.isArchived = isArchived
        self.idTask = idTask
        self.guarantor = guarantor
        self.deletedUser1 = deletedUser1
        self.deletedUser2 = deletedUser2

    def __repr__(self):
        return f"<conversation ({self.idUser1}, {self.idUser2}, {self.guarantor}, {self.idTask}, {self.isArchived}, {self.deletedUser1}, {self.deletedUser2})>"