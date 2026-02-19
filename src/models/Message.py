from app import db
from sqlalchemy.dialects.mysql import INTEGER, TEXT
import datetime

class Message(db.Model):
    __tablename__ = "message"

    idMessage = db.Column(INTEGER(unsigned=True), primary_key = True)
    idConversation = db.Column(INTEGER(unsigned=True), nullable = False)
    idUser1 = db.Column(INTEGER(unsigned=True), nullable = False)
    idUser2 = db.Column(INTEGER(unsigned=True), nullable = False)
    sender = db.Column(INTEGER(unsigned=True), nullable = False)
    message = db.Column(TEXT, nullable = False)
    createdAt = db.Column(db.DateTime(timezone=True), default=lambda:datetime.datetime.now(datetime.timezone.utc), nullable=False)
    replyToMessage = db.Column(INTEGER(unsigned=True), nullable = True)

    __table_args__ = (
        db.ForeignKeyConstraint(
            ["idConversation", "idUser1", "idUser2"],
            ["conversation.idConversation", "conversation.idUser1", "conversation.idUser2"],
            ondelete="CASCADE"
        ),
    )

    def __init__(self, idMessage, idConversation, sender, message, replyToMessage, idUser1, idUser2):
        self.idMessage = idMessage
        self.idConversation = idConversation
        self.replyToMessage = replyToMessage
        self.sender = sender
        self.message = message
        self.idUser1 = idUser1
        self.idUser2 = idUser2

    def __repr__(self):
        return f"<message ({self.idMessage}, {self.idConversation}, {self.message}, {self.sender}, {self.replyToMessage}, {self.createdAt}, {self.idUser1}, {self.idUser2})>"