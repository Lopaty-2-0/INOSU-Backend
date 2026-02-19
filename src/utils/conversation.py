from src.models.Conversation import Conversation
from app import db
from sqlalchemy import or_, and_

def create_conversation(idUser1, idUser2, idTask, guarantor):
    conversationForId = Conversation.query.filter(or_(and_(Conversation.idUser1 == idUser1, Conversation.idUser2 == idUser2), and_(Conversation.idUser1 == idUser2, Conversation.idUser2 == idUser1))).order_by(Conversation.idConversation.desc()).first()

    id = conversationForId.idConversation + 1 if conversationForId else 1

    newConversation = Conversation(id, idUser1, idUser2, idTask, guarantor, False, False, False)
    db.session.add(newConversation)
    db.session.commit()

    return newConversation