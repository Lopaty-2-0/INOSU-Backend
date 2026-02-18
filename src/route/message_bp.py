from flask import Blueprint, request
from src.models.Conversation import Conversation
from src.models.Message import Message
import flask_login
from src.utils.response import send_response
from app import max_INT, db, max_TEXT
from src.utils.message import create_message
from src.models.User import User
from sqlalchemy import or_
from src.utils.all_user_classes import all_user_classes
from src.models.Task import Task
from src.email.templates.conversation_message import email_conversation_message
from src.utils.send_email import send_email

message_bp = Blueprint("message_bp", __name__)

@message_bp.route("/message/add", methods = ["POST"])
@flask_login.login_required
def add():
    data = request.get_json(force=True)
    idConversation = data.get("idConversation", None)
    message = data.get("message", None)
    replyToMessage = data.get("replyToMessage", None)
    replyToMessageData = None

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

    if message >= max_TEXT:
        return send_response(400, 87050, {"message": "message too long"}, "error")
    
    conversation = Conversation.query.filter_by(idConversation = idConversation).first()

    if not conversation:
        return send_response(404, 87060, {"message": "conversation not found"}, "error")
    
    if conversation.idUser1 != flask_login.current_user.id and conversation.idUser2 != flask_login.current_user.id:
        return send_response(400, 87070, {"message": "this user does not have access to this conversation"}, "error")
    
    if replyToMessage:
        try:
            replyToMessage = int(replyToMessage)
        except:
            return send_response(400, 87080, {"message": "replyToMessage not integer"}, "error")
        if replyToMessage > max_INT or replyToMessage <= 0:
            return send_response(400, 87090, {"message": "replyToMessage not valid"}, "error")
        
        replyMessage = Message.query.filter_by(idConversation = idConversation, idMessage = replyToMessage).first()

        if not replyMessage:
            return send_response(404, 87100, {"message": "nonexistent message"}, "error")
        
        sender = User.query.filter_by(id = replyMessage.sender).first()
        replyToMessageData = {"idMessage":replyMessage.idMessage, "message":replyMessage.message, "createdAt":replyMessage.createdAt, "replyToMessage":replyMessage.replyToMessage, "sender":{"id": sender.id, "name": sender.name, "surname": sender.surname, "abbreviation": sender.abbreviation, "role": sender.role.value, "profilePicture": sender.profilePicture, "email": sender.email, "idClass": all_user_classes(sender.id), "createdAt":sender.createdAt, "updatedAt":sender.updatedAt, "reminders":sender.reminders}}
        
    if conversation.isArchived:
        return send_response(400, 87110, {"message": "Can not write to this conversation"}, "error")
    
    if conversation.idTask:
        if conversation.idUser1 == flask_login.current_user.id:
            user = User.query.filter_by(id = conversation.idUser2).first()
        else:
            user = User.query.filter_by(id = conversation.idUser1).first()
        
        task = Task.query.filter_by(id = conversation.idTask, guarantor = conversation.guarantor).first()
        html = email_conversation_message(user.name + " " + user.surname, flask_login.current_user.name + " " + flask_login.current_user.surname, task.name)
        text = f"Došla zpráva od uživatele: {flask_login.current_user.name + " " + flask_login.current_user.surname}. Pro úkol: {task.name}"
        send_email(user.email, "Incoming message", html, text)

    newMessage = create_message(idConversation, flask_login.current_user.id, message, replyToMessage)

    senderData = {
        "id": flask_login.current_user.id, 
        "name": flask_login.current_user.name, 
        "surname": flask_login.current_user.surname, 
        "abbreviation": flask_login.current_user.abbreviation, 
        "role": flask_login.current_user.role.value, 
        "profilePicture": flask_login.current_user.profilePicture, 
        "email": flask_login.current_user.email, 
        "idClass": all_user_classes(flask_login.current_user.id), 
        "createdAt": flask_login.current_user.createdAt, 
        "updatedAt": flask_login.current_user.updatedAt, 
        "reminders": flask_login.current_user.reminders
    }

    return send_response(200, 87121, {"message": "Message sent successfuly", "newMessage":{"idMessage":newMessage.idMessage, "idConversation":newMessage.idConversation, "message": newMessage.message, "createdAt":newMessage.createdAt, "sender": senderData, "replyToMessage":replyToMessageData}}, "success")
    
@message_bp.route("/message/delete", methods = ["DELETE"])
@flask_login.login_required
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
    
@message_bp.route("/message/get", methods = ["GET"])
@flask_login.login_required
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
    
    messages = Message.query.filter_by(idConversation = idConversation).order_by(Message.idMessage.desc()).offset(amountForPaging * pageNumber).limit(amountForPaging).all()
    count =  Message.query.filter_by(idConversation = idConversation).count()

    for i in range(len(messages), 0, -1):
        message = messages[i-1]
        replyMessageData = None
        user = User.query.filter_by(id = message.sender).first()

        if message.replyToMessage:
            replyMessage = Message.query.filter_by(idMessage = message.replyToMessage, idConversation = idConversation).first()
            sender = User.query.filter_by(id = replyMessage.sender).first()
            replyMessageData = {"idMessage":replyMessage.idMessage, "message":replyMessage.message, "createdAt":replyMessage.createdAt, "replyToMessage":replyMessage.replyToMessage, "sender":{"id": sender.id, "name": sender.name, "surname": sender.surname, "abbreviation": sender.abbreviation, "role": sender.role.value, "profilePicture": sender.profilePicture, "email": sender.email, "idClass": all_user_classes(sender.id), "createdAt":sender.createdAt, "updatedAt":sender.updatedAt, "reminders":sender.reminders}}

        allMessages.append({"idMessage":message.idMessage, "message":message.message, "createdAt":message.createdAt, "replyToMessage":replyMessageData, "sender":{"id": user.id, "name": user.name, "surname": user.surname, "abbreviation": user.abbreviation, "role": user.role.value, "profilePicture": user.profilePicture, "email": user.email, "idClass": all_user_classes(user.id), "createdAt":user.createdAt, "updatedAt":user.updatedAt, "reminders":user.reminders}})

    return send_response(200, 60131, {"message": "Messages for conversation found successfuly", "messages":allMessages, "count":count}, "success")

