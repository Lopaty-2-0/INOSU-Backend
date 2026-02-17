from src.models.Conversation import Conversation
from app import db

def create_conversation(idUser1, idUser2, idTask, guarantor):
    newConversation = Conversation(idUser1, idUser2, idTask, guarantor, False, False, False)
    db.session.add(newConversation)
    db.session.commit()

    return newConversation