from flask import request, Blueprint
import flask_login
import datetime
from app import db, max_INT
from src.models.User_Team import User_Team
from src.models.Task import Task
from src.models.User_Class import User_Class
from src.models.User import User
from src.models.Team import Team
from src.utils.enums import Status, Type, Role
from src.utils.team import make_team
from src.utils.response import send_response
from src.models.Version_Team import Version_Team
from src.utils.reminder import create_reminder, cancel_reminder
from src.utils.paging import user_team_paging
from sqlalchemy import and_, or_
from src.utils.version import delete_upload_version
from src.models.Conversation import Conversation
from src.utils.archive_conversation import cancel_archive_conversation

user_team_bp = Blueprint("user_team", __name__)


@user_team_bp.route("/user_team/add", methods=["POST"])
@flask_login.login_required
def add():
    data = request.get_json(force=True)
    idTask = data.get("idTask", None)
    idUser = data.get("idUser", None)
    idClass = data.get("idClass", None)
    idTeam = data.get("idTeam", None)
    badIds = []
    goodIds = []
    differentTeam = []

    if not idTask:
        return send_response(400, 36010, {"message": "idTask not entered"}, "error")
    if not idUser and not idClass:
        return send_response(400, 36020, {"message": "idUser or idClass not entered"}, "error")
    try:
        idTask = int(idTask)
    except:
        return send_response(400, 36030, {"message": "idTask not integer"}, "error")
    if idTask > max_INT or idTask <= 0:
        return send_response(400, 36040, {"message": "idTask not valid"}, "error")
    task = Task.query.filter_by(id=idTask, guarantor = flask_login.current_user.id).first()
    if not task:
        return send_response(404, 36050, {"message": "Nonexistent task"}, "error")
    if task.type == Type.Maturita and User_Team.query.filter_by(idTask=idTask, guarantor = flask_login.current_user.id).first():
        return send_response(400, 36060, {"message": "This maturita task already has user"}, "error")

    status = Status.Approved

    if not isinstance(idUser, list) and idUser:
        idUser = [idUser]
    if not isinstance(idClass, list) and idClass:
        idClass = [idClass]

    if not idTeam:
        if idUser and not idClass:
            for idU in idUser:
                if task.type == Type.Maturita and User_Team.query.filter_by(idTask = idTask, guarantor = flask_login.current_user.id).first():
                    break
                try:
                    idU = int(idU)
                except:
                    badIds.append(idU)
                    continue
                if idU > max_INT or idU <= 0:
                    badIds.append(idU)
                    continue

                if not User.query.filter_by(id=idU).first() or User.query.filter_by(id = id).role != Role.Student:
                    badIds.append(idU)
                    continue

                if User_Team.query.filter_by(idUser = idU, idTask = idTask, guarantor = flask_login.current_user.id).first():
                    differentTeam.append(idU)
                    continue

                idT = make_team(idTask = idTask, status = status, name = None, isTeam = False, guarantor = flask_login.current_user.id)

                newUser_Team = User_Team(idUser = idU, idTask = idTask, idTeam = idT, guarantor = flask_login.current_user.id)
                db.session.add(newUser_Team)

                if User.query.filter_by(id=idU).first().reminders:
                    create_reminder(idUser = idU, idTask = idTask, guarantor = flask_login.current_user.id)

                goodIds.append(idU)

        if idClass and not idUser:
            for idCl in idClass:
                if task.type == Type.Maturita and User_Team.query.filter_by(idTask = idTask, guarantor = flask_login.current_user.id).first():
                    break
                try:
                    idCl = int(idCl)
                except:
                    badIds.append(idCl)
                    continue
                if idCl > max_INT or idCl <= 0:
                    badIds.append(idCl)
                    continue

                users = User_Class.query.filter_by(idClass = idCl)

                for user in users:
                    idU = user.idUser

                    if not User.query.filter_by(id=idU).first():
                        badIds.append(idU)
                        continue
                    if User_Team.query.filter_by(idUser = idU, idTask = idTask, guarantor = flask_login.current_user.id).first():
                        differentTeam.append(idU)
                        continue

                    idT = make_team(idTask = idTask, status = status, name = None, isTeam = False, guarantor = flask_login.current_user.id)

                    newUser_Team = User_Team(idUser = idU, idTask = idTask, idTeam = idT, guarantor = flask_login.current_user.id)
                    db.session.add(newUser_Team)

                    if  User.query.filter_by(id=idU).first().reminders:
                        create_reminder(idUser = idU, idTask = idTask, guarantor = flask_login.current_user.id)

                goodIds.append(idCl)

    else:
        for idU in idUser:
            if task.type == Type.Maturita and User_Team.query.filter_by(idTask = idTask, guarantor = flask_login.current_user.id).first():
                    break
            try:
                idU = int(idU)
            except:
                badIds.append(idU)
                continue
            if idU > max_INT or idU <= 0:
                badIds.append(idU)
                continue
            if not User.query.filter_by(id=idU).first() or not Team.query.filter_by(idTeam = idTeam, idTask = idTask, guarantor = flask_login.current_user.id).first():
                badIds.append(idU)
                continue
            if User_Team.query.filter_by(idUser = idU, idTask = idTask, guarantor = flask_login.current_user.id).first():
                differentTeam.append(idU)
                continue

            newUser_Team = User_Team(idUser = idU, idTask = idTask, idTeam = idTeam, guarantor = flask_login.current_user.id)
            db.session.add(newUser_Team)
            goodIds.append(idU)

            if User.query.filter_by(id=idU).first().reminders:
                create_reminder(idUser = idU, idTask = idTask, guarantor = flask_login.current_user.id)
                
    db.session.commit()

    if not goodIds and not differentTeam:
        return send_response(400, 36070, {"message": "Nothing created"}, "error")

    return send_response(201, 36081, {"message": "user_team created successfuly","badIds":badIds, "goodIds":goodIds, "differentTeam":differentTeam}, "success")

@user_team_bp.route("/user_team/delete", methods=["DELETE"])
@flask_login.login_required
def delete():
    data = request.get_json(force=True)
    idTask = data.get("idTask", None)
    idUser = data.get("idUser", None)
    idTeam = data.get("idTeam", None)

    if not idTask:
        return send_response(400, 37010, {"message": "idTask not entered"}, "error")
    if not idUser:
        return send_response(400, 37020, {"message": "idUser not entered"}, "error")
    if not idTeam:
        return send_response(400, 37030, {"message": "idTeam not entered"}, "error")
    try:
        idTask = int(idTask)
    except:
        return send_response(400, 37040, {"message": "idTask not integer"}, "error")
    
    if idTask > max_INT or idTask <= 0:
        return send_response(400, 37050, {"message": "idTask not valid"}, "error")
    if not Task.query.filter_by(id=idTask, guarantor = flask_login.current_user.id).first():
        return send_response(404, 37060, {"message": "Nonexistent task"}, "error")

    try:
        idUser = int(idUser)
    except:
        return send_response(400, 37070, {"message": "idUser not integer"}, "error")
    
    if idUser > max_INT or idUser <= 0:
        return send_response(400, 37080, {"message": "idUser not valid"}, "error")
    if not User.query.filter_by(id=idUser).first():
        return send_response(404, 37090, {"message": "Nonexistent USER"}, "error")
    
    try:
        idTeam = int(idTeam)
    except:
        return send_response(400, 37100, {"message": "idTeam not integer"}, "error")
    
    if idTeam > max_INT or idTeam <= 0:
        return send_response(400, 37110, {"message": "idTeam not valid"}, "error")
    if not Team.query.filter_by(idTask=idTask, guarantor = flask_login.current_user.id, idTeam = idTeam).first():
        return send_response(404, 37120, {"message": "Nonexistent team"}, "error")
    
    userTeam = User_Team.query.filter_by(idTask = idTask, idUser = idUser, idTeam = idTeam, guarantor = flask_login.current_user.id).first()

    if not userTeam:
        return send_response(404, 37130, {"message": "Nonexistent user_team"}, "error")
    
    if Task.query.filter_by(id=idTask, guarantor = flask_login.current_user.id).first().type == Type.Maturita:
        conversation = Conversation.query.filter(or_(Conversation.idUser1 == idUser, Conversation.idUser2 == idUser), Conversation.idTask == idTask, Conversation.guarantor == flask_login.current_user.id).first()

        if conversation:
            cancel_archive_conversation(conversation.idConversation, conversation.idTask, conversation.guarantor, conversation.idUser1, conversation.idUser2)
            db.session.delete(conversation)

    db.session.delete(userTeam)
    db.session.commit()

    cancel_reminder(idUser = idUser, idTask = idTask, guarantor = flask_login.current_user.id)

    return send_response(200, 37141, {"message": "user_team deleted successfuly"}, "success")

@user_team_bp.route("/user_team/get", methods=["GET"])
@flask_login.login_required
def get():
    amountForPaging = request.args.get("amountForPaging", None)
    pageNumber = request.args.get("pageNumber", None)
    searchQuery = request.args.get("searchQuery", None)
    
    rightUserTeams = []
    if not amountForPaging:
        return send_response(400, 39010, {"message": "amountForPaging not entered"}, "error")

    try:
        amountForPaging = int(amountForPaging)
    except:
        return send_response(400, 39020, {"message": "amountForPaging not integer"}, "error")
    
    if amountForPaging < 1:
        return send_response(400, 39030, {"message": "amountForPaging smaller than 1"}, "error")
    
    if amountForPaging > max_INT:
        return send_response(400, 39040, {"message": "amountForPaging too big"}, "error")
    
    if not pageNumber:
        return send_response(400, 39050, {"message": "pageNumber not entered"}, "error")
    
    try:
        pageNumber = int(pageNumber)
    except:
        return send_response(400, 39060, {"message": "pageNumber not integer"}, "error")
    if pageNumber > max_INT + 1:
        return send_response(400, 39070, {"message": "pageNumber too big"}, "error")
    
    pageNumber -= 1

    if pageNumber < 0:
        return send_response(400, 39080, {"message": "pageNumber must be bigger than 0"}, "error")
    
    if not searchQuery:
        userTeams = User_Team.query.filter_by(idUser = flask_login.current_user.id).join(Task, and_(Task.guarantor == User_Team.guarantor, Task.id == User_Team.idTask)).where(Task.type == Type.Task).order_by(User_Team.idTask.desc()).offset(amountForPaging * pageNumber).limit(amountForPaging)
        count = userTeams.count()
    else:
        userTeams, count = user_team_paging(searchQuery = searchQuery, amountForPaging = amountForPaging, pageNumber = pageNumber, idUser = flask_login.current_user.id, taskType = Type.Task)

    for userTeam in userTeams:
        
        task = Task.query.filter_by(id = userTeam.idTask, guarantor = userTeam.guarantor).first()
        user = User.query.filter_by(id = task.guarantor).first()
        team = Team.query.filter_by(idTeam = userTeam.idTeam, idTask = userTeam.idTask, guarantor = userTeam.guarantor).first()
        version = Version_Team.query.filter_by(idTeam = userTeam.idTeam, idTask = userTeam.idTask, guarantor = userTeam.guarantor).order_by(Version_Team.idVersion.desc()).first()

        if not version:
            elaboration = None
            createdAt = None
        else:
            elaboration = version.elaboration
            createdAt = version.createdAt

        guarantor = {
                    "id":user.id, 
                    "name":user.name, 
                    "surname": user.surname, 
                    "abbreviation": user.abbreviation, 
                    "createdAt": user.createdAt, 
                    "role": user.role.value, 
                    "profilePicture":user.profilePicture, 
                    "email":user.email, 
                    "updatedAt":user.updatedAt
                    }
        rightUserTeams.append({
                                "idTask":userTeam.idTask, 
                                "name":task.name, 
                                "startDate":task.startDate, 
                                "endDate":task.endDate, 
                                "task":task.task, 
                                "guarantor":guarantor,
                                "points":task.points,
                                "team":{
                                        "idTeam":userTeam.idTeam, 
                                        "status":team.status.value, 
                                        "elaboration":elaboration,
                                        "createdAt":createdAt, 
                                        "review":team.review, 
                                        "name":team.name, 
                                        "points":team.points
                                        }
                                })
        
    return send_response(200, 39091, {"message": "User_teams found", "user_teams":rightUserTeams, "count":count}, "success")


@user_team_bp.route("/user_team/change", methods=["PUT"])
@flask_login.login_required
def change():
    data = request.get_json(force=True)
    idTask = data.get("idTask", None)
    idUser = data.get("idUser", None)
    idTeam = data.get("idTeam", None)
    goodIds = []
    badIds = []
    ids = []
    differentTeam = []

    if not idTask:
        return send_response(400, 43010, {"message": "idTask not entered"}, "error")
    if not idTeam:
        return send_response(400, 43020, {"message": "idTeam not entered"}, "error")
    try:
        idTask = int(idTask)
    except:
        return send_response(400, 43030, {"message": "idTask not integer"}, "error")
    
    if idTask > max_INT or idTask <= 0:
        return send_response(400, 43040, {"message": "idTask not valid"}, "error")

    try:
        idTeam = int(idTeam)
    except:
        return send_response(400, 43050, {"message": "idTeam not integer"}, "error")
    
    if idTeam > max_INT or idTeam <= 0:
        return send_response(400, 43060, {"message": "idTeam not valid"}, "error")
    
    task = Task.query.filter_by(id=idTask, guarantor = flask_login.current_user.id).first()

    if not task:
        return send_response(404, 43070, {"message": "Nonexistent task"}, "error")
    
    team = Team.query.filter_by(idTeam = idTeam, idTask = idTask, guarantor = flask_login.current_user.id).first()

    if not team:
        return send_response(404, 43080, {"message": "Nonexistent team"}, "error")
    if not isinstance(idUser, list):
        idUser = [idUser]

    if len(idUser) > 1 and not team.isTeam:
        return send_response(403, 43090, {"message": "Can not add more users into this team"}, "error")
    
    user_teams = User_Team.query.filter_by(idTask = idTask, idTeam = idTeam, guarantor = flask_login.current_user.id)

    for user_team in user_teams:
        db.session.delete(user_team)
        ids.append(user_team.idUser)

        cancel_reminder(idUser = user_team.idUser, idTask = idTask, guarantor = flask_login.current_user.id)

    for id in idUser:
        if task.type == Type.Maturita and id in goodIds:
            break
        try:
            id = int(id)
        except:
            badIds.append(id)
            continue
        if id > max_INT or id <= 0 or not User.query.filter_by(id = id).first() or User.query.filter_by(id = id).first().role != Role.Student:
            badIds.append(id)
            continue
        if User_Team.query.filter_by(idUser = id, idTask = idTask, guarantor = flask_login.current_user.id).first():
            differentTeam.append(id)
            continue

        db.session.add(User_Team(idUser = id, idTeam = idTeam, idTask = idTask, guarantor = flask_login.current_user.id))
        goodIds.append(id)

        if id in ids:
            ids.pop(ids.index(id))

        if User.query.filter_by(id = id).first().reminders:
            create_reminder(idUser = id, idTask = idTask, guarantor = flask_login.current_user.id)

    if task.type == Type.Maturita:
        for convId in ids:
            conversation = Conversation.query.filter(or_(Conversation.idUser1 == convId, Conversation.idUser2 == convId), Conversation.idTask == idTask, Conversation.guarantor == flask_login.current_user.id).first()
            
            if conversation:
                db.session.delete(conversation)
        
    if not team.isTeam and not User_Team.query.filter_by(idTeam = idTeam, idTask = idTask).first():
        versions = Version_Team.query.filter_by(idTask = idTask, idTeam = idTeam, guarantor = flask_login.current_user.id)

        for version in versions:
            if version.elaboration:
                delete_upload_version(version.idTask, version.idTeam, version.elaboration, version.guarantor, version.idVersion)

        db.session.delete(team)

    db.session.commit()

    return send_response(200, 43101, {"message": "user_teams changed", "badIds":badIds, "goodIds":goodIds, "differentTeam": differentTeam}, "success")

@user_team_bp.route("/user_team/count/tasks", methods=["GET"])
@flask_login.login_required
def count_user_tasks():
    userTeams = User_Team.query.filter_by(idUser=flask_login.current_user.id).all()
    now = datetime.datetime.now(datetime.timezone.utc)
    count = 0

    for userTeam in userTeams:
        task = Task.query.filter_by(id = userTeam.idTask, guarantor = userTeam.guarantor).first()

        if task.type == Type.Maturita:
            continue

        endTime = task.deadline if task.deadline else task.endDate
        if not endTime:
            continue

        if now > endTime.replace(tzinfo=datetime.timezone.utc):
            continue
        
        count += 1

    return send_response(200, 47011, { "message": "Count of user tasks", "count": count }, "success")
