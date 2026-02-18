from flask import Blueprint, request
from src.models.Task import Task
from src.models.User_Team import User_Team
from src.models.User import User
from src.models.Conversation import Conversation
from src.models.Message import Message
import flask_login
from src.utils.response import send_response
from app import max_INT, db
from sqlalchemy import or_, and_
from src.utils.conversation import create_conversation
from src.utils.all_user_classes import all_user_classes
from src.utils.enums import Type, Role
from src.models.Maturita_Task import Maturita_Task
from src.models.Maturita import Maturita
import datetime
from src.utils.archive_conversation import create_archive_conversation

conversation_bp = Blueprint("conversation_bp", __name__)

@conversation_bp.route("/conversation/add", methods = ["POST"])
@flask_login.login_required
def add():
    data = request.get_json(force=True)
    idUser = data.get("idUser", None)
    idTask = data.get("idTask", None)
    guarantor = data.get("guarantor", None)

    if not idUser:
        return send_response(400, 86010, {"message": "idUser missing"}, "error")
    try:
        idUser = int(idUser)
    except:
        return send_response(400, 86020, {"message": "idUser not integer"}, "error")
    if idUser > max_INT or idUser <= 0:
        return send_response(400, 86030, {"message": "idUser not valid"}, "error")

    
    user = User.query.filter_by(id = idUser).first()

    if not user:
        return send_response(404, 86040, {"message": "Nonexistent user"}, "error")
    
    if idUser == flask_login.current_user.id:
        return send_response(400, 86050, {"message": "Can not make a conversation with this user"}, "error")
    
    if idTask and guarantor:
        now = datetime.datetime.now(datetime.timezone.utc)
        try:
            idTask = int(idTask)
        except:
            return send_response(400, 86060, {"message": "idTask not integer"}, "error")
        if idTask > max_INT or idTask <= 0:
            return send_response(400, 86070, {"message": "idTask not valid"}, "error")
        try:
            guarantor = int(guarantor)
        except:
            return send_response(400, 86080, {"message": "guarantor not integer"}, "error")
        if guarantor > max_INT or guarantor <= 0:
            return send_response(400, 86090, {"message": "guarantor not valid"}, "error")
        
        task = Task.query.filter_by(id = idTask, guarantor = guarantor).first()

        if not task:
            return send_response(404, 86100, {"message": "Nonexistent task"}, "error")
        if task.type != Type.Maturita:
            return send_response(400, 86110, {"message": "Can not add conversation for non maturita task"}, "error")
        if Maturita_Task.query.join(Maturita, (Maturita.id == Maturita_Task.idMaturita)).filter(Maturita_Task.idTask == idTask, Maturita_Task.guarantor == guarantor, Maturita.startDate <= now, now <= Maturita.endDate).first():
            return send_response(400, 86120, {"message": "Can not add conversation for a task that is past endDate"}, "error")
        if (flask_login.current_user.id != guarantor and idUser != guarantor) or (not User_Team.query.filter(User_Team.idTask == idTask, User_Team.guarantor == guarantor, or_(User_Team.idUser == flask_login.current_user.id, User_Team.idUser == idUser)).first()):
            return send_response(400, 86130, {"message": "these users can not make conversation for this task"}, "error")
    else:
        idTask = None
        guarantor = None

    if Conversation.query.filter(or_(and_(Conversation.idUser1 == flask_login.current_user.id, Conversation.idUser2 == idUser), and_(Conversation.idUser2 == flask_login.current_user.id, Conversation.idUser1 == idUser)), Conversation.idTask == idTask, Conversation.guarantor == guarantor).first():
        return send_response(400, 86140, {"message": "these users already have conversation"}, "error")
    
    conversation = create_conversation(flask_login.current_user.id, idUser, idTask, guarantor)

    if idTask and guarantor and user.role == Role.Student:
        create_archive_conversation(conversation.idConversation, idTask, guarantor)

    return send_response(201, 86151, {"message": "Conversation created successfuly", "conversation":{"idConversation": conversation.idConversation, "idTask":conversation.idTask, "guarantor":conversation.guarantor, "idUser1":conversation.idUser1, "idUser2":conversation.idUser2}}, "success")

@conversation_bp.route("/conversation/delete", methods = ["DELETE"])
@flask_login.login_required
def delete():
    data = request.get_json(force=True)
    idConversation = data.get("idConversation", None)

    if not idConversation:
        return send_response(400, 87010, {"message": "idConversation missing"}, "error")
    try:
        idConversation = int(idConversation)
    except:
        return send_response(400, 87020, {"message": "idConversation not integer"}, "error")
    if idConversation > max_INT or idConversation <= 0:
        return send_response(400, 87030, {"message": "idConversation not valid"}, "error")
    
    conversation = Conversation.query.filter(Conversation.idConversation == idConversation, or_(Conversation.idUser1 == flask_login.current_user.id, Conversation.idUser2 == flask_login.current_user.id)).first()
    
    if not conversation or conversation.idTask:
        return send_response(400, 87040, {"message": "Conversation not found or can not be deleted"}, "error")
    
    if conversation.idUser1 == flask_login.current_user.id:
        conversation.idUser1 = None
    else:
        conversation.idUser2 = None

    senderMessages = Message.query.filter_by(idConversation = idConversation, sender = flask_login.current_user.id)

    for senderMessage in senderMessages:
        senderMessage.sender = None
    db.session.commit()

    if not conversation.idUser1 and not conversation.idUser2:
        db.session.delete(conversation)
        db.session.commit()

    return send_response(200, 87051, {"message": "Conversation deleted successfuly for current user"}, "success")

@conversation_bp.route("/conversation/get", methods = ["GET"])
@flask_login.login_required
def get():
    amountForPaging = request.args.get("amountForPaging", None)
    pageNumber = request.args.get("pageNumber", None)

    allConversations = []

    if not amountForPaging:
        return send_response(400, 89010, {"message": "amountForPaging not entered"}, "error")

    try:
        amountForPaging = int(amountForPaging)
    except:
        return send_response(400, 89020, {"message": "amountForPaging not integer"}, "error")
    
    if amountForPaging < 1:
        return send_response(400, 89030, {"message": "amountForPaging smaller than 1"}, "error")
    
    if amountForPaging > max_INT:
        return send_response(400, 89040, {"message": "amountForPaging too big"}, "error")
    
    if not pageNumber:
        return send_response(400, 89050, {"message": "pageNumber not entered"}, "error")
    
    try:
        pageNumber = int(pageNumber)
    except:
        return send_response(400, 89060, {"message": "pageNumber not integer"}, "error")
    if pageNumber > max_INT + 1:
        return send_response(400, 89070, {"message": "pageNumber too big"}, "error")
    
    pageNumber -= 1

    if pageNumber < 0:
        return send_response(400, 89080, {"message": "pageNumber must be bigger than 0"}, "error")
    
    conversations = Conversation.query.filter(or_(Conversation.idUser1 == flask_login.current_user.id, Conversation.idUser2 == flask_login.current_user.id), Conversation.idTask == None).offset(pageNumber * amountForPaging).limit(amountForPaging)
    count = Conversation.query.filter(or_(Conversation.idUser1 == flask_login.current_user.id, Conversation.idUser2 == flask_login.current_user.id), Conversation.idTask == None).count()
    
    for conversation in conversations:
        task = None
        if conversation.idUser1 == flask_login.current_user.id:
            user = User.query.filter_by(id = conversation.idUser2).first()
        else:
            user = User.query.filter_by(id = conversation.idUser1).first()

        if conversation.idTask:
            foundTask = Task.query.filter(id = conversation.idTask, guarantor = conversation.guarantor).first()
            guarantorUser = User.query.filter(id = conversation.guarantor).first()

            guarantor = {"id": guarantorUser.id, "name": guarantorUser.name, "surname": guarantorUser.surname, "abbreviation": guarantorUser.abbreviation, "role": guarantorUser.role.value, "profilePicture": guarantorUser.profilePicture, "email": guarantorUser.email, "idClass": all_user_classes(guarantorUser.id), "createdAt":guarantorUser.createdAt, "updatedAt":guarantorUser.updatedAt, "reminders":guarantorUser.reminders}
            task = {
                "id": foundTask.id,
                "name": foundTask.name,
                "startDate": foundTask.startDate,
                "endDate": foundTask.endDate,
                "task": foundTask.task,
                "deadline": foundTask.deadline,
                "guarantor":guarantor,
            }

        allConversations.append({"idConversation":conversation.idConversation, "user":{"id": user.id, "name": user.name, "surname": user.surname, "abbreviation": user.abbreviation, "role": user.role.value, "profilePicture": user.profilePicture, "email": user.email, "idClass": all_user_classes(user.id), "createdAt":user.createdAt, "updatedAt":user.updatedAt, "reminders":user.reminders}, "task":task, "isArchived":conversation.isArchived})

    return send_response(200, 89091, {"message": "Conversations found successfuly", "conversations":allConversations, "count":count}, "success")

@conversation_bp.route("/conversation/get/guarantor", methods = ["GET"])
@flask_login.login_required
def get_guarantor():
    idTask = request.args.get("idTask", None)
    
    if not idTask:
       return send_response(400, 90010, {"message": "idTask not entered"}, "error")
    try:
        idTask = int(idTask)
    except:
        return send_response(400, 90020, {"message": "idTask not integer"}, "error")
    if idTask > max_INT or idTask <= 0:
        return send_response(400, 90030, {"message": "idTask not valid"}, "error")
    
    foundTask = Task.query.filter_by(id = idTask, guarantor = flask_login.current_user.id).first()

    if not foundTask:
       return send_response(404, 90040, {"message": "task not found"}, "error")
    
    task = {
        "id": foundTask.id,
        "name": foundTask.name,
        "startDate": foundTask.startDate,
        "endDate": foundTask.endDate,
        "task": foundTask.task,
        "deadline": foundTask.deadline,
        }
    conversations = Conversation.query.filter(or_(Conversation.idUser1 == flask_login.current_user.id, Conversation.idUser2 == flask_login.current_user.id), Conversation.idTask == idTask, Conversation.guarantor == flask_login.current_user.id)
    
    for conversation in conversations:
        objectorConversation = None
        studentConversation = None

        if conversation.idUser1 == flask_login.current_user.id:
            user = User.query.filter_by(id = conversation.idUser2).first()
        else:
            user = User.query.filter_by(id = conversation.idUser1).first()

        maturita = Maturita_Task.query.filter_by(idTask = idTask, guarantor = flask_login.current_user.id).first()

        if not maturita:
            return send_response(400, 90050, {"message": "For this type of task can not exist conversations"}, "error")
        
        if user.id == maturita.objector:
            objectorConversation = {"idConversation":conversation.idConversation, "user":{"id": user.id, "name": user.name, "surname": user.surname, "abbreviation": user.abbreviation, "role": user.role.value, "profilePicture": user.profilePicture, "email": user.email, "idClass": all_user_classes(user.id), "createdAt":user.createdAt, "updatedAt":user.updatedAt, "reminders":user.reminders}, "task":task, "isArchived":conversation.isArchived}
        else:
            studentConversation = {"idConversation":conversation.idConversation, "user":{"id": user.id, "name": user.name, "surname": user.surname, "abbreviation": user.abbreviation, "role": user.role.value, "profilePicture": user.profilePicture, "email": user.email, "idClass": all_user_classes(user.id), "createdAt":user.createdAt, "updatedAt":user.updatedAt, "reminders":user.reminders}, "task":task, "isArchived":conversation.isArchived}

    return send_response(200, 90061, {"message": "Conversations found successfuly", "objectorConversation":objectorConversation, "studentConversation":studentConversation}, "success")

@conversation_bp.route("/conversation/get/participant", methods = ["GET"])
@flask_login.login_required
def get_participant():
    idTask = request.args.get("idTask", None)
    guarantor = request.args.get("guarantor", None)
    
    if not idTask:
       return send_response(400, 27010, {"message": "idTask not entered"}, "error")
    try:
        idTask = int(idTask)
    except:
        return send_response(400, 27020, {"message": "idTask not integer"}, "error")
    if idTask > max_INT or idTask <= 0:
        return send_response(400, 27030, {"message": "idTask not valid"}, "error")
    if not guarantor:
       return send_response(400, 27040, {"message": "guarantor not entered"}, "error")
    try:
        guarantor = int(guarantor)
    except:
        return send_response(400, 27050, {"message": "guarantor not integer"}, "error")
    if guarantor > max_INT or guarantor <= 0:
        return send_response(400, 27060, {"message": "guarantor not valid"}, "error")
    
    foundTask = Task.query.filter_by(id = idTask, guarantor = guarantor).first()

    if not foundTask:
       return send_response(404, 27070, {"message": "task not found"}, "error")
    
    if guarantor == flask_login.current_user.id:
        return send_response(400, 27080, {"message": "This route is not for this user"}, "error")
    
    task = {
        "id": foundTask.id,
        "name": foundTask.name,
        "startDate": foundTask.startDate,
        "endDate": foundTask.endDate,
        "task": foundTask.task,
        "deadline": foundTask.deadline,
    }
    
    conversation = Conversation.query.filter(or_(Conversation.idUser1 == flask_login.current_user.id, Conversation.idUser2 == flask_login.current_user.id), Conversation.idTask == idTask, Conversation.guarantor == guarantor).first()
    
    if not conversation:
        return send_response(404, 27090, {"message": "conversation not found"}, "error")
    
    if conversation.idUser1 == flask_login.current_user.id:
        user = User.query.filter_by(id = conversation.idUser2).first()
    else:
        user = User.query.filter_by(id = conversation.idUser1).first()

    maturita = Maturita_Task.query.filter_by(idTask = idTask, guarantor = guarantor).first()

    if not maturita:
        return send_response(400, 27100, {"message": "For this type of task can not exist conversations"}, "error")
    
    conversationData = {"idConversation":conversation.idConversation, "user":{"id": user.id, "name": user.name, "surname": user.surname, "abbreviation": user.abbreviation, "role": user.role.value, "profilePicture": user.profilePicture, "email": user.email, "idClass": all_user_classes(user.id), "createdAt":user.createdAt, "updatedAt":user.updatedAt, "reminders":user.reminders}, "task":task, "isArchived":conversation.isArchived}

    return send_response(200, 27111, {"message": "Conversations found successfuly", "conversation":conversationData}, "success")

@conversation_bp.route("/conversation/get/id", methods = ["GET"])
@flask_login.login_required
def get_id():
    idConversation = request.args.get("idConversation", None)
    task = None

    if not idConversation:
        return send_response(400, 91010, {"message": "idConversation missing"}, "error")
    try:
        idConversation = int(idConversation)
    except:
        return send_response(400, 91020, {"message": "idConversation not integer"}, "error")
    if idConversation > max_INT or idConversation <= 0:
        return send_response(400, 91030, {"message": "idConversation not valid"}, "error")
    
    conversation = Conversation.query.filter(Conversation.idConversation == idConversation, or_(Conversation.idUser1 == flask_login.current_user.id, Conversation.idUser2 == flask_login.current_user.id)).first()
    
    if not conversation:
        return send_response(404, 91040, {"message": "Conversation not found"}, "error")
    
    if conversation.idUser1 == flask_login.current_user.id:
        user = User.query.filter_by(id = conversation.idUser2).first()
    else:
        user = User.query.filter_by(id = conversation.idUser1).first()

    foundTask = Task.query.filter_by(id = conversation.idTask, guarantor = conversation.guarantor).first()

    if foundTask:
        task = {
            "id": foundTask.id,
            "name": foundTask.name,
            "startDate": foundTask.startDate,
            "endDate": foundTask.endDate,
            "task": foundTask.task,
            "deadline": foundTask.deadline,
        }
    
    conversationData = {"idConversation":conversation.idConversation, "user":{"id": user.id, "name": user.name, "surname": user.surname, "abbreviation": user.abbreviation, "role": user.role.value, "profilePicture": user.profilePicture, "email": user.email, "idClass": all_user_classes(user.id), "createdAt":user.createdAt, "updatedAt":user.updatedAt, "reminders":user.reminders}, "task":task, "isArchived":conversation.isArchived}

    return send_response(200, 91051, {"message": "Conversation found successfuly", "conversation": conversationData}, "success")