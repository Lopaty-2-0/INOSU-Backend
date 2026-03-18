from src.models.Message import Message
from src.models.Conversation import Conversation
from app import db
from sqlalchemy import and_, or_

def create_message(idConversation, sender, message, replyToMessage, idUser):
    conversation = Conversation.query.filter(and_(Conversation.idConversation == idConversation, or_(and_(Conversation.idUser1 == sender, Conversation.idUser2 == idUser), and_(Conversation.idUser1 == idUser, Conversation.idUser2 == sender)))).order_by(Conversation.idConversation.desc()).first()

    if not conversation:
        return
    
    messageForId = Message.query.filter(Message.idConversation == conversation.idConversation, Message.idUser1 == conversation.idUser1, Message.idUser2 == conversation.idUser2).order_by(Message.idMessage.desc()).first()

    id = messageForId.idMessage + 1 if messageForId else 1

    newMessage = Message(id, idConversation, sender, message, replyToMessage, conversation.idUser1, conversation.idUser2)
    db.session.add(newMessage)
    db.session.commit()

    return newMessage