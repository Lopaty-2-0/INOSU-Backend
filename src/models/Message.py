from app import db
from sqlalchemy.dialects.mysql import INTEGER, TEXT
import datetime

class Message(db.Model):
    __tablename__ = "message"

    idMessage = db.Column(INTEGER(unsigned=True), primary_key = True)
    idConversation = db.Column(INTEGER(unsigned=True), db.ForeignKey("conversation.idConversation", ondelete = "CASCADE"), primary_key = True)
    sender = db.Column(INTEGER(unsigned=True), db.ForeignKey("user.id"), nullable = True)
    message = db.Column(TEXT, nullable = False)
    createdAt = db.Column(db.DateTime(timezone=True), default=lambda:datetime.datetime.now(datetime.timezone.utc), nullable=False)
    replyToMessage = db.Column(INTEGER(unsigned=True), nullable = True)

    def __init__(self, idMessage, idConversation, sender, message, replyToMessage):
        self.idMessage = idMessage
        self.idConversation = idConversation
        self.replyToMessage = replyToMessage
        self.sender = sender
        self.message = message

    def __repr__(self):
        return f"<message ({self.idMessage}, {self.idConversation}, {self.message}, {self.sender}, {self.replyToMessage}, {self.createdAt})>"