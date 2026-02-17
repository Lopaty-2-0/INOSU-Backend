from src.models.Message import Message
from app import db

def create_message(idConversation, sender, message, replyToMessage):
    messageForId = Message.query.filter_by(idConversation = idConversation).order_by(Message.idMessage.desc()).first()

    id = messageForId.id + 1 if messageForId else 1

    newMessage = Message(id, idConversation, sender, message, replyToMessage)
    db.session.add(newMessage)
    db.session.commit()

    return newMessage