from flask import Blueprint, request
from src.models.Conversation import Conversation
from src.models.Message import Message
import flask_login
from src.utils.response import send_response
from app import max_INT, db
from src.utils.message import create_message
from src.models.User import User
from sqlalchemy import or_
from src.utils.all_user_classes import all_user_classes

message_bp = Blueprint("message_bp", __name__)

@flask_login.login_required
@message_bp.route("/message/add", methods = ["POST"])
def add():
    data = request.get_json(force=True)
    idConversation = data.get("idConversation", None)
    message = data.get("message", None)
    replyToMessage = data.get("replyToMessage", None)

    if not idConversation:
        return send_response(400, 87010, {"message": "idConversation missing"}, "error")
    try:
        idConversation = int(idConversation)
    except:
        return send_response(400, 87020, {"message": "idConversation not integer"}, "error")
    if idConversation > max_INT or idConversation <= 0:
        return send_response(400, 87030, {"message": "idConversation not valid"}, "error")
    if not message:
        return send_response(400, 87040, {"message": "message missing"}, "error")
    
    message = str(message)
    
    conversation = Conversation.query.filter_by(idConversation = idConversation).first()

    if not conversation:
        return send_response(404, 87050, {"message": "conversation not found"}, "error")
    
    if conversation.idUser1 != flask_login.current_user.id and conversation.idUser2 != flask_login.current_user.id:
        return send_response(400, 87060, {"message": "this user does not have access to this conversation"}, "error")
    
    if replyToMessage:
        try:
            replyToMessage = int(replyToMessage)
        except:
            return send_response(400, 87070, {"message": "replyToMessage not integer"}, "error")
        if replyToMessage > max_INT or replyToMessage <= 0:
            return send_response(400, 87080, {"message": "replyToMessage not valid"}, "error")
        if not Message.query.filter_by(idConversation = idConversation, idMessage = replyToMessage).first():
            return send_response(404, 87090, {"message": "nonexistent message"}, "error")
        
    
    if conversation.isArchived:
        return send_response(400, 87100, {"message": "Can not write to this conversation"}, "error")

    newMessage = create_message(idConversation, flask_login.current_user.id, message, replyToMessage)

    return send_response(200, 87111, {"message": "Message sent successfuly", "message":{"idMessage":newMessage.idMessage, "idConversation":newMessage.idConversation, "createdAt":newMessage.createdAt, "sender":newMessage.sender, "replyToMessage":newMessage.replyToMessage}}, "success")
    

@flask_login.login_required
@message_bp.route("/message/delete", methods = ["DELETE"])
def delete():
    data = request.get_json(force=True)
    idConversation = data.get("idConversation", None)
    idMessage = data.get("idMessage", None)

    if not idConversation:
        return send_response(400, 88010, {"message": "idConversation missing"}, "error")
    if not idMessage:
        return send_response(400, 88020, {"message": "idMessage missing"}, "error")
    try:
        idConversation = int(idConversation)
    except:
        return send_response(400, 88030, {"message": "idConversation not integer"}, "error")
    if idConversation > max_INT or idConversation <= 0:
        return send_response(400, 88040, {"message": "idConversation not valid"}, "error")
    try:
        idMessage = int(idMessage)
    except:
        return send_response(400, 88050, {"message": "idMessage not integer"}, "error")
    if idMessage > max_INT or idMessage <= 0:
        return send_response(400, 88060, {"message": "idMessage not valid"}, "error")

    conversation = Conversation.query.filter_by(idConversation = idConversation).first()

    if not conversation:
        return send_response(404, 88070, {"message": "conversation not found"}, "error")
    
    if conversation.idUser1 != flask_login.current_user.id and conversation.idUser2 != flask_login.current_user.id:
        return send_response(400, 88080, {"message": "this user does not have access to this conversation"}, "error")
    
    if conversation.isArchived:
        return send_response(400, 88090, {"message": "can not delete message in this conversation"}, "error")
    
    message = Message.query.filter_by(idConversation = idConversation, idMessage = idMessage).first()
    
    if not message:
        return send_response(404, 88100, {"message": "message not found"}, "error")
    
    if message.sender != flask_login.current_user.id:
        return send_response(400, 88110, {"message": "can not delete this message"}, "error")
    
    replyMessages = Message.query.filter_by(idConversation = idConversation, replyToMessage = idMessage)

    for replyMessage in replyMessages:
        replyMessage.replyToMessage = None
    
    db.session.delete(message)
    db.session.commit()

    return send_response(200, 88121, {"message": "Message deleted successfuly"}, "success")
    
@flask_login.login_required
@message_bp.route("/message/get", methods = ["GET"])
def get_messages():
    idConversation = request.args.get("idConversation", None)
    amountForPaging = request.args.get("amountForPaging", None)
    pageNumber = request.args.get("pageNumber", None)

    allMessages = []

    if not amountForPaging:
        return send_response(400, 60010, {"message": "amountForPaging not entered"}, "error")

    try:
        amountForPaging = int(amountForPaging)
    except:
        return send_response(400, 60020, {"message": "amountForPaging not integer"}, "error")
    
    if amountForPaging < 1:
        return send_response(400, 60030, {"message": "amountForPaging smaller than 1"}, "error")
    
    if amountForPaging > max_INT:
        return send_response(400, 60040, {"message": "amountForPaging too big"}, "error")
    
    if not pageNumber:
        return send_response(400, 60050, {"message": "pageNumber not entered"}, "error")
    
    try:
        pageNumber = int(pageNumber)
    except:
        return send_response(400, 60060, {"message": "pageNumber not integer"}, "error")
    if pageNumber > max_INT + 1:
        return send_response(400, 60070, {"message": "pageNumber too big"}, "error")
    
    pageNumber -= 1

    if pageNumber < 0:
        return send_response(400, 60080, {"message": "pageNumber must be bigger than 0"}, "error")

    if not idConversation:
       return send_response(400, 60090, {"message": "idConversation not entered"}, "error")
    try:
        idConversation = int(idConversation)
    except:
        return send_response(400, 60100, {"message": "idConversation not integer"}, "error")
    if idConversation > max_INT or idConversation <= 0:
        return send_response(400, 60110, {"message": "idConversation not valid"}, "error")
    
    conversation = Conversation.query.filter(Conversation.idConversation == idConversation, or_(Conversation.idUser1 == flask_login.current_user.id, Conversation.idUser2 == flask_login.current_user.id)).first()

    if not conversation:
        return send_response(404, 60120, {"message": "conversation not found"}, "error")
    
    messages = Message.query.filter_by(idConversation = idConversation).order_by(Message.idMessage.asc()).offset(amountForPaging * pageNumber).limit(amountForPaging)
    count =  Message.query.filter_by(idConversation = idConversation).count()

    for message in messages:
        replyMessageData = None
        user = User.query.filter_by(id = message.sender).first()
        if message.replyToMessage:
            replyMessage = Message.query.filter_by(idMessage = message.replyToMessage, idConversation = idConversation).first()
            sender = User.query.filter_by(id = replyMessage.sender).first()
            replyMessageData = {"idMessage":replyMessage.idMessage, "message":replyMessage.message, "createdAt":replyMessage.createdAt, "replyToMessage":replyMessage.replyToMessage, "sender":{"id": sender.id, "name": sender.name, "surname": sender.surname, "abbreviation": sender.abbreviation, "role": sender.role.value, "profilePicture": sender.profilePicture, "email": sender.email, "idClass": all_user_classes(sender.id), "createdAt":sender.createdAt, "updatedAt":sender.updatedAt, "reminders":sender.reminders}}

        allMessages.append({"idMessage":message.idMessage, "message":message.message, "createdAt":message.createdAt, "replyToMessage":replyMessageData, "sender":{"id": user.id, "name": user.name, "surname": user.surname, "abbreviation": user.abbreviation, "role": user.role.value, "profilePicture": user.profilePicture, "email": user.email, "idClass": all_user_classes(user.id), "createdAt":user.createdAt, "updatedAt":user.updatedAt, "reminders":user.reminders}})

    return send_response(200, 60131, {"message": "Messages for conversation found successfuly", "messages":allMessages, "count":count}, "success")

