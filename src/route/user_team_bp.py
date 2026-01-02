from flask import request, Blueprint
import flask_login
from app import db, maxINT, scheduler
from src.models.User_Team import User_Team
from src.models.Task import Task
from src.models.User_Class import User_Class
from src.models.User import User
from src.models.Team import Team
from src.utils.enums import Status, Type
from src.utils.team import make_team, team_deleteDir
from src.utils.response import send_response
from src.models.Version_Team import Version_Team
from src.utils.reminder import create_reminder, cancel_reminder
from src.utils.paging import user_team_paging
from sqlalchemy import and_

user_team_bp = Blueprint("user_team", __name__)

@user_team_bp.route("/user_team/add", methods=["POST"])
@flask_login.login_required
async def add():
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
    if idTask > maxINT or idTask <= 0:
        return send_response(400, 36040, {"message": "idTask not valid"}, "error")
    if not Task.query.filter_by(id=idTask).first():
        return send_response(400, 36050, {"message": "Nonexistent task"}, "error")
    if flask_login.current_user.id != Task.query.filter_by(id = idTask).first().guarantor:
        return send_response(400, 36060, {"message": "User is not a guarantor"}, "error")
    if not idClass and Task.query.filter_by(id = idTask).first().type == Type.Maturita:
        status = Status.Pending
    else:
        status = Status.Approved


    if not isinstance(idUser, list) and idUser:
        idUser = [idUser]
    if not isinstance(idClass, list) and idClass:
        idClass = [idClass]

    if not idTeam:
        if idUser and not idClass:
            for idU in idUser:
                try:
                    idU = int(idU)
                except:
                    badIds.append(idU)
                    continue
                if idU > maxINT or idU <= 0:
                    badIds.append(idU)
                    continue

                if not User.query.filter_by(id=idU).first():
                    badIds.append(idU)
                    continue

                if User_Team.query.filter_by(idUser = idU, idTask = idTask).first():
                    differentTeam.append(idU)
                    continue

                idT = await make_team(idTask = idTask, status = status, name = None, isTeam = False)

                newUser_Team = User_Team(idUser = idU, idTask = idTask, idTeam = idT)
                db.session.add(newUser_Team)

                if User.query.filter_by(id=idU).first().reminders:
                    create_reminder(idUser = idU, idTask = idTask)

                goodIds.append(idU)

        if idClass and not idUser:
            for idCl in idClass:
                try:
                    idCl = int(idCl)
                except:
                    badIds.append(idCl)
                    continue
                if idCl > maxINT or idCl <= 0:
                    badIds.append(idCl)
                    continue

                users = User_Class.query.filter_by(idClass = idCl)

                for user in users:
                    idU = user.idUser

                    if not User.query.filter_by(id=idU).first():
                        badIds.append(idU)
                        continue
                    if User_Team.query.filter_by(idUser = idU, idTask = idTask).first():
                        differentTeam.append(idU)
                        continue

                    idT = await make_team(idTask = idTask, status = status, name = None, isTeam = False)

                    newUser_Team = User_Team(idUser = idU, idTask = idTask, idTeam = idT)
                    db.session.add(newUser_Team)

                    if  User.query.filter_by(id=idU).first().reminders:
                        create_reminder(idUser = idU, idTask = idTask)

                goodIds.append(idCl)

    else:
        for idU in idUser:
            try:
                idU = int(idU)
            except:
                badIds.append(idU)
                continue
            if idU > maxINT or idU <= 0:
                badIds.append(idU)
                continue
            if not User.query.filter_by(id=idU).first() or not Team.query.filter_by(idTeam = idTeam, idTask = idTask).first():
                badIds.append(idU)
                continue
            if User_Team.query.filter_by(idUser = idU, idTask = idTask).first():
                differentTeam.append(idU)
                continue

            newUser_Team = User_Team(idUser = idU, idTask = idTask, idTeam = idTeam)
            db.session.add(newUser_Team)
            goodIds.append(idU)

            if User.query.filter_by(id=idU).first().reminders:
                create_reminder(idUser = idU, idTask = idTask)
                
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
    
    if idTask > maxINT or idTask <= 0:
        return send_response(400, 37050, {"message": "idTask not valid"}, "error")

    try:
        idUser = int(idUser)
    except:
        return send_response(400, 37060, {"message": "idUser not integer"}, "error")
    
    if idUser > maxINT or idUser <= 0:
        return send_response(400, 37070, {"message": "idUser not valid"}, "error")
    
    try:
        idTeam = int(idTeam)
    except:
        return send_response(400, 37080, {"message": "idTeam not integer"}, "error")
    
    if idTeam > maxINT or idTeam <= 0:
        return send_response(400, 37090, {"message": "idTeam not valid"}, "error")

    
    user_team = User_Team.query.filter_by(idTask = idTask, idUser = idUser, idTeam = idTeam).first()

    if not user_team:
        return send_response(400, 37100, {"message": "Nonexistent user_team"}, "error")

    db.session.delete(user_team)
    db.session.commit()

    cancel_reminder(idUser = idUser, idTask = idTask)

    return send_response(200, 37111, {"message": "user_team deleted successfuly"}, "success")

@user_team_bp.route("/user_team/get", methods=["GET"])
@flask_login.login_required
def get():
    idUser = request.args.get("idUser", None)
    amountForPaging = request.args.get("amountForPaging", None)
    pageNumber = request.args.get("pageNumber", None)
    
    right_user_teams = []
    if not amountForPaging:
        return send_response(400, 39010, {"message": "amountForPaging not entered"}, "error")

    try:
        amountForPaging = int(amountForPaging)
    except:
        return send_response(400, 39020, {"message": "amountForPaging not integer"}, "error")
    
    if amountForPaging < 1:
        return send_response(400, 39030, {"message": "amountForPaging smaller than 1"}, "error")
    
    if amountForPaging > maxINT:
        return send_response(400, 39040, {"message": "amountForPaging too big"}, "error")
    
    if not pageNumber:
        return send_response(400, 39050, {"message": "pageNumber not entered"}, "error")
    
    try:
        pageNumber = int(pageNumber)
    except:
        return send_response(400, 39060, {"message": "pageNumber not integer"}, "error")
    if pageNumber > maxINT + 1:
        return send_response(400, 39070, {"message": "pageNumber too big"}, "error")
    
    pageNumber -= 1

    if pageNumber < 0:
        return send_response(400, 39080, {"message": "pageNumber must be bigger than 0"}, "error")
    
    if not idUser:
        return send_response(400, 39090, {"message": "idUser not entered"}, "error")
    try:
        idUser = int(idUser)
    except:
        return send_response(400, 39100, {"message": "idUser not integer"}, "error")
    
    if idUser > maxINT or idUser <= 0:
        return send_response(400, 39110, {"message": "idUser not valid"}, "error")
    if not User.query.filter_by(id = idUser).first():
        return send_response(400, 39120, {"message": "Nonexistent user"}, "error")
    
    user_teams = User_Team.query.filter_by(idUser = idUser).offset(amountForPaging * pageNumber).limit(amountForPaging)
    count = user_teams.count()

    for user_team in user_teams:
        
        task = Task.query.filter_by(id = user_team.idTask).first()
        user = User.query.filter_by(id = task.guarantor).first()
        team = Team.query.filter_by(idTeam = user_team.idTeam, idTask = user_team.idTask).first()
        version = Version_Team.query.filter_by(idTeam = user_team.idTeam, idTask = user_team.idTask).order_by(Version_Team.idVersion.desc()).first()

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
        right_user_teams.append({
                                "idTask":user_team.idTask, 
                                "name":task.name, 
                                "startDate":task.startDate, 
                                "endDate":task.endDate, 
                                "task":task.task, 
                                "guarantor":guarantor,
                                "team":{
                                        "idTeam":user_team.idTeam, 
                                        "status":team.status.value, 
                                        "elaboration":elaboration,
                                        "createdAt":createdAt, 
                                        "review":team.review, 
                                        "name":team.name, 
                                        "points":team.points
                                        }
                                })
        
    return send_response(200, 39131, {"message": "User_teams found", "user_teams":right_user_teams, "count":count}, "success")


@user_team_bp.route("/user_team/change", methods=["PUT"])
@flask_login.login_required
async def change():
    data = request.get_json(force=True)
    idTask = data.get("idTask", None)
    idUser = data.get("idUser", None)
    idTeam = data.get("idTeam", None)
    goodIds = []
    badIds = []
    differentTeam = []

    if not idTask:
        return send_response(400, 43010, {"message": "idTask not entered"}, "error")
    if not idTeam:
        return send_response(400, 43020, {"message": "idTeam not entered"}, "error")
    try:
        idTask = int(idTask)
    except:
        return send_response(400, 43030, {"message": "idTask not integer"}, "error")
    
    if idTask > maxINT or idTask <= 0:
        return send_response(400, 43040, {"message": "idTask not valid"}, "error")

    try:
        idTeam = int(idTeam)
    except:
        return send_response(400, 43050, {"message": "idTeam not integer"}, "error")
    
    if idTeam > maxINT or idTeam <= 0:
        return send_response(400, 43060, {"message": "idTeam not valid"}, "error")
    if not Task.query.filter_by(id=idTask).first():
        return send_response(400, 43070, {"message": "Nonexistent task"}, "error")
    
    team = Team.query.filter_by(idTeam = idTeam, idTask = idTask).first()

    if not team:
        return send_response(400, 43080, {"message": "Nonexistent team"}, "error")
    if flask_login.current_user.id != Task.query.filter_by(id = idTask).first().guarantor:
        return send_response(403, 43090, {"message": "No permission"}, "error")
    if not isinstance(idUser, list):
        idUser = [idUser]

    if len(idUser) > 1 and not team.isTeam:
        return send_response(403, 43100, {"message": "Can not add more users into this team"}, "error")
    
    user_teams = User_Team.query.filter_by(idTask = idTask, idTeam = idTeam)

    for user_team in user_teams:
        db.session.delete(user_team)

        cancel_reminder(idUser = user_team.idUser, idTask = idTask)

    for id in idUser:
        try:
            id = int(id)
        except:
            badIds.append(id)
            continue
        if id > maxINT or id <= 0 or not User.query.filter_by(id = id).first():
            badIds.append(id)
            continue
        if User_Team.query.filter_by(idUser = id, idTask = idTask).first():
            differentTeam.append(id)
            continue

        db.session.add(User_Team(idUser = id, idTeam = idTeam, idTask = idTask))
        goodIds.append(id)

        if User.query.filter_by(id = id).first().reminders:
            create_reminder(idUser = id, idTask = idTask)
    
    if not team.isTeam and not User_Team.query.filter_by(idTeam = idTeam, idTask = idTask).first():
        versions = Version_Team.query.filter_by(idTask = idTask, idTeam = idTeam)

        for version in versions:
            db.session.delete(version)
        
        db.session.commit()
        db.session.delete(team)

        await team_deleteDir(idTeam = idTeam, idTask = idTask)
    db.session.commit()

    return send_response(200, 43111, {"message": "user_teams changed", "badIds":badIds, "goodIds":goodIds, "differentTeam": differentTeam}, "success")

@user_team_bp.route("/user_team/count/approved_without_review", methods=["GET"])
@flask_login.login_required
def count_approved_without_review():
    count = 0
    user_team = User_Team.query.filter_by(idUser = flask_login.current_user.id)

    for team in user_team:
        if Team.query.filter_by(idTeam = team.idTeam, idTask = team.idTask).review == None:
            count += 1

    return send_response(200, 47011, {"message": "Count of approved user_teams without review", "count": count}, "success")

@user_team_bp.route("/user_team/get/type", methods = ["GET"])
@flask_login.login_required
def get_by_type():
    amountForPaging = request.args.get("amountForPaging", None)
    pageNumber = request.args.get("pageNumber", None)
    searchQuery = request.args.get("searchQuery", None)
    taskType = request.args.get("taskType", None)
    return_tasks = []

    if not amountForPaging:
        return send_response(400, 60010, {"message": "amountForPaging not entered"}, "error")

    try:
        amountForPaging = int(amountForPaging)
    except:
        return send_response(400, 60020, {"message": "amountForPaging not integer"}, "error")
    
    if amountForPaging < 1:
        return send_response(400, 60030, {"message": "amountForPaging smaller than 1"}, "error")
    
    if amountForPaging > maxINT:
        return send_response(400, 60040, {"message": "amountForPaging too big"}, "error")
    
    if not pageNumber:
        return send_response(400, 60050, {"message": "pageNumber not entered"}, "error")
    
    try:
        pageNumber = int(pageNumber)
    except:
        return send_response(400, 60060, {"message": "pageNumber not integer"}, "error")
    if pageNumber > maxINT + 1:
        return send_response(400, 60070, {"message": "pageNumber too big"}, "error")
    
    pageNumber -= 1

    if pageNumber < 0:
        return send_response(400, 60080, {"message": "pageNumber must be bigger than 0"}, "error")
    
    if not taskType:
        return send_response(400, 60090, {"message": "taskType not entered"}, "error")
    
    if taskType not in [t.value for t in Type]:
        return send_response(400, 60100, {"message": "taskType not our type"}, "error")
    
    if not searchQuery:      
        teams = Team.query.join(User_Team, Team.idTeam == User_Team.idTeam).join(Task, Team.idTask == Task.id).filter(and_(User_Team.idUser == flask_login.current_user.id, Task.type == Type(taskType))).group_by(Team.idTeam, Team.idTask).offset(amountForPaging * pageNumber).limit(amountForPaging)
        count = Team.query.join(User_Team, Team.idTeam == User_Team.idTeam).join(Task, Team.idTask == Task.id).filter(and_(User_Team.idUser == flask_login.current_user.id, Task.type == Type(taskType))).group_by(Team.idTeam, Team.idTask).count()
    else:
        teams, count = user_team_paging(searchQuery = searchQuery, pageNumber = pageNumber, amountForPaging = amountForPaging, idUser = flask_login.current_user.id, taskType = taskType)

    for team in teams:
        task = Task.query.filter_by(id = team.idTask).first()
        user = User.query.filter_by(id = task.guarantor).first()
        version = Version_Team.query.filter_by(idTask=team.idTask, idTeam = team.idTeam).order_by(Version_Team.idVersion.desc()).first()

        if not version:
            elaboration = None
            createdAt = None
        else:
            elaboration = version.elaboration
            createdAt = version.createdAt

        return_team = {
                        "idTeam":team.idTeam,
                        "points":team.points,
                        "review":team.review,
                        "status":team.status.value,
                        "name":team.name,
                        "isTeam":team.isTeam,
                        "reviewUpdatedAt":team.reviewUpdatedAt,
                        "teamUpdatedAt":team.teamUpdatedAt,
                        "elaboration":elaboration,
                        "createdAt":createdAt
                        }
    
        guarantor = {
                    "id":user.id,
                    "name":user.name,
                    "surname": user.surname,
                    "abbreviation": user.abbreviation,
                    "createdAt": user.createdAt,
                    "role": user.role.value,
                    "profilePicture":user.profilePicture,
                    "email":user.email
                    }

        return_tasks.append({"idTask":task.id, "name":task.name, "startDate":task.startDate, "endDate":task.endDate, "deadline":task.deadline, "task":task.task, "guarantor":guarantor, "type":task.type.value, "points":task.points, "team":return_team})
    
    return send_response(200, 60111, {"message": "All task for current user in this type", "tasks":return_tasks, "count":count}, "success")