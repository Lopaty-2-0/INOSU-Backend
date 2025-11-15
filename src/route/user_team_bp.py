from flask import request, Blueprint
import flask_login
import json
from app import db
from src.models.User_Team import User_Team
from src.models.Task import Task
from src.models.User_Class import User_Class
from src.models.User import User
from src.models.Team import Team
from src.utils.enums import Status, Type
from src.utils.team import make_team
from src.utils.response import send_response
from src.utils.team import team_createDir
from src.utils.all_user_classes import all_user_classes
from urllib.parse import unquote
from src.models.Version_Team import Version_Team

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

    if not idTask:
        return send_response(400, 36010, {"message": "idTask not entered"}, "error")
    if not idUser:
        return send_response(400, 36020, {"message": "idUser not entered"}, "error")
    if not Task.query.filter_by(id=idTask).first():
        return send_response(400, 36030, {"message": "Nonexistent task"}, "error")
    if not flask_login.current_user.id == Task.query.filter_by(id = idTask).first().guarantor:
        return send_response(400, 36040, {"message": "User is not a guarantor"}, "error")
    if not idClass and Task.query.filter_by(id = idTask).first().type == Type.Maturita:
        status = Status.Pending
    else:
        status = Status.Approved


    if not isinstance(idUser, list):
        idUser = [idUser]
    if not isinstance(idClass, list):
        idClass = [idClass]

    if not idTeam:
        if idUser and not idClass:
            for idU in idUser:
                if User_Team.query.filter_by(idUser = idU, idTask = idTask).first() or not User.query.filter_by(id=idU).first():
                    badIds.append(idU)
                    continue

                idT = await make_team(idTask = idTask, status = status, name = None)

                newUser_Team = User_Team(idUser = idU, idTask = idTask, idTeam = idT)
                await team_createDir(idTask, idT)
                db.session.add(newUser_Team)
                goodIds.append(idU)

        if idClass and not idUser:
            for idCl in idClass:
                users = User_Class.query.filter_by(idClass = idCl)

                for user in users:
                    idU = user.id

                    if User_Team.query.filter_by(idUser = idU, idTask = idTask).first() or not User.query.filter_by(id=idU).first():
                        badIds.append(idU)
                        continue

                    idT = await make_team(idTask = idTask, status = status, name = None)

                    newUser_Team = User_Team(idUser = idU, idTask = idTask, idTeam = idT)
                    await team_createDir(idTask, idT)
                    db.session.add(newUser_Team)
                    goodIds.append(idU)
    else:
        for idU in idUser:
            if User_Team.query.filter_by(idUser = idU, idTask = idTask).first() or not User.query.filter_by(id=idU).first():
                badIds.append(idU)
                continue

            newUser_Team = User_Team(idUser = idU, idTask = idTask, idTeam = idTeam)
            db.session.add(newUser_Team)
            goodIds.append(idU)

    if not goodIds:
        return send_response(400, 36040, {"message": "Nothing created"}, "error")

    db.session.commit()

    return send_response(201, 36051, {"message": "user_team created successfuly","badIds":badIds, "goodIds":goodIds}, "success")

@user_team_bp.route("/user_team/delete", methods=["DELETE"])
@flask_login.login_required
def delete():
    data = request.get_json(force=True)
    idTask = data.get("idTask", None)
    idUser = data.get("idUser", None)

    if not idTask:
        return send_response(400, 37010, {"message": "idTask not entered"}, "error")
    if not idUser:
        return send_response(400, 37020, {"message": "idUser not entered"}, "error")
    
    user_team = User_Team.query.filter_by(idTask = idTask, idUser = idUser).first()

    if not user_team:
        return send_response(400, 37030, {"message": "Nonexistent user_team"}, "error")

    db.session.delete(user_team)
    db.session.commit()

    return send_response(200, 37041, {"message": "user_team deleted successfuly"}, "success")

#TODO: zjistit co si o tom náš pán myslí
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
    
    if not pageNumber:
        return send_response(400, 39040, {"message": "pageNumber not entered"}, "error")
    
    try:
        pageNumber = int(pageNumber)
    except:
        return send_response(400, 39050, {"message": "pageNumber not integer"}, "error")
    
    pageNumber -= 1

    if pageNumber < 0:
        return send_response(400, 39060, {"message": "pageNumber must be bigger than 0"}, "error")
    
    if not idUser:
        return send_response(400, 39070, {"message": "idUser not entered"}, "error")
    if not User.query.filter_by(id = idUser).first():
        return send_response(400, 39080, {"message": "Nonexistent user"}, "error")
    
    user_teams = User_Team.query.filter_by(idUser = idUser).offset(amountForPaging * pageNumber).limit(amountForPaging)

    if not user_teams:
        return send_response(400, 39090, {"message":"No user_teams found"}, "error")
    
    count = user_teams.count()

    for user_team in user_teams:
        
        task = Task.query.filter_by(id = user_team.idTask).first()
        user = User.query.filter_by(id = task.guarantor).first()
        team = Team.query.filter_by(idTeam = user_team.idTeam, idTask = user_team.idTask).first()
        version = Version_Team.query.filter_by(idTeam = user_team.idTeam, idTask = user_team.idTask).order_by(Version_Team.idVersion.desc()).first()
        if not version:
            elaboration = None
        else:
            elaboration = version.elaboration
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
                                        "review":team.review, 
                                        "name":team.name, 
                                        "points":team.points
                                        }
                                })
        
    return send_response(200, 39101, {"message": "User_teams found", "user_teams":right_user_teams, "count":count}, "success")


#TODO: vymyslet lépe ten paging
@user_team_bp.route("/user_team/get/status/elaboration", methods=["GET"])
@flask_login.login_required
def get_by_status_elaboration(): 
    status = request.args.get("status", "")
    amountForPaging = request.args.get("amountForPaging", None)
    pageNumber = request.args.get("pageNumber", None)
    elaboratingTasks = []
    goodStatuses = []
    
    if not amountForPaging:
        return send_response(400, 53010, {"message": "amountForPaging not entered"}, "error")
    
    try:
        amountForPaging = int(amountForPaging)
    except:
        return send_response(400, 53020, {"message": "amountForPaging not integer"}, "error")
    
    if amountForPaging < 1:
        return send_response(400, 53030, {"message": "amountForPaging smaller than 1"}, "error")
    
    if not pageNumber:
        return send_response(400, 53040, {"message": "pageNumber not entered"}, "error")
    
    try:
        pageNumber = int(pageNumber)
    except:
        return send_response(400, 53050, {"message": "pageNumber not integer"}, "error")
    
    pageNumber -= 1

    if pageNumber < 0:
        return send_response(400, 53060, {"message": "pageNumber must be bigger than 0"}, "error")
    
    try:
        decoded_status = unquote(status)
        status = json.loads(decoded_status) if decoded_status.strip() else []
    except:
        status = []

    if not isinstance(status, list):
        status = [status]

    for s in status:
        if s in [stat.value for stat in Status]:
            goodStatuses.append(s)

    for s in goodStatuses:
        user_teams = User_Team.query.filter_by(idUser = flask_login.current_user.id).offset(amountForPaging * pageNumber).limit(amountForPaging)

        for user_team in user_teams:
            team = Team.query.filter_by(idTask = user_team.idTask, idTeam = user_team.idTeam).first()
            task = Task.query.filter_by(id = user_team.idTask).first()
            user = User.query.filter_by(id = task.guarantor).first()
            version = Version_Team.query.filter_by(idTask=user_team.idTask, idTeam = user_team.idTeam).order_by(Version_Team.idVersion.desc()).first()

            if not version:
                elaboration = None
            else:
                elaboration = version.elaboration

            elaboratingTasks.append({"team":{
                                            "idTeam":team.idTeam,
                                            "status":team.status.value,
                                            "elaboration":elaboration, 
                                            "review":team.review, 
                                            "name":team.name, 
                                            "points":team.points, 
                                            },
                                    "task":task.task,
                                    "name":task.name, 
                                    "statDate":task.startDate, 
                                    "endDate":task.endDate, 
                                    "type":task.type.value, 
                                    "guarantor":{"id": user.id, 
                                                    "name": user.name, 
                                                    "surname": user.surname, 
                                                    "abbreviation": user.abbreviation, 
                                                    "role": user.role.value, 
                                                    "profilePicture": user.profilePicture, 
                                                    "email": user.email, 
                                                    "idClass": all_user_classes(user.id), 
                                                    "createdAt":user.createdAt,
                                                    "updatedAt":user.updatedAt
                                                },
                                    "idTask":task.id,
                                    "taskPoints":task.points,
                                    })
    if not elaboratingTasks:
        return send_response(400, 53070, {"message": "No elaboratingTasks found"}, "error")
                
    return send_response(200, 53021, {"message": "All tasks with these statuses for current user", "elaboratingTasks":elaboratingTasks}, "success")

#TODO: předělat na paging (za mne úplně zbytečný route)
"""@user_team_bp.route("/user_team/get/idTask", methods=["GET"])
@flask_login.login_required
def get_by_idTask():
    idTask = request.args.get("idTask", None)
    amountForPaging = request.args.get("amountForPaging", None)
    pageNumber = request.args.get("pageNumber", None)
    users = []
    teams = []
    
    if not amountForPaging:
        return send_response(400, 53010, {"message": "amountForPaging not entered"}, "error")
    
    try:
        amountForPaging = int(amountForPaging)
    except:
        return send_response(400, 53020, {"message": "amountForPaging not integer"}, "error")
    
    if amountForPaging < 1:
        return send_response(400, 53030, {"message": "amountForPaging smaller than 1"}, "error")
    
    if not pageNumber:
        return send_response(400, 53040, {"message": "pageNumber not entered"}, "error")
    
    try:
        pageNumber = int(pageNumber)
    except:
        return send_response(400, 53050, {"message": "pageNumber not integer"}, "error")
    
    pageNumber -= 1

    if pageNumber < 0:
        return send_response(400, 53060, {"message": "pageNumber must be bigger than 0"}, "error")
    

    if not idTask:
        return send_response(400, 42010, {"message": "idTask not entered"}, "error")
    if not Task.query.filter_by(id = idTask).first():
        return send_response(400, 42020, {"message": "Nonexistent task"}, "error")
    
    team = User_Team.query.filter_by(idTask = idTask)

    if not team:
        return send_response(400, 42030, {"message": "No user has this task"}, "error")

    for t in team:
        user = User.query.filter_by(id = t.idUser).offset(amountForPaging * pageNumber).limit(amountForPaging)
        users.append(user.id)

    return send_response(200, 42041, {"message": "Users found", "users":users}, "success")"""

@user_team_bp.route("/user_team/change", methods=["PUT"])
@flask_login.login_required
async def change():
    data = request.get_json(force=True)
    idTask = data.get("idTask", None)
    idUser = data.get("idUser", None)
    idTeam = data.get("idTeam", None)
    goodIds = []
    badIds = []
    ids = []
    removedIds = []

    if not idTask:
        return send_response(400, 43010, {"message": "idTask not entered"}, "error")
    if not idUser:
        return send_response(400, 43020, {"message": "idUser not entered"}, "error")
    if not idTeam:
        return send_response(400, 43030, {"message": "idTeam not entered"}, "error")
    if not Task.query.filter_by(id=idTask).first():
        return send_response(400, 43040, {"message": "Nonexistent task"}, "error")
    if not Team.query.filter_by(idTeam = idTeam, idTask = idTask).first():
        return send_response(400, 43050, {"message": "Nonexistent team"}, "error")
    if flask_login.current_user.id != Task.query.filter_by(id = idTask).first().guarantor:
        return send_response(403, 43060, {"message": "No permission"}, "error")
    if not isinstance(idUser, list):
        idUser = [idUser]
    
    user_team = User_Team.query.filter_by(idTask = idTask, idTeam = idTeam)

    for id in idUser:
        if not User.query.filter_by(id = id).first():
            badIds.append(id)
            continue
        ids.append(id)

    for team in user_team:
        if not team.idUser in ids:
            db.session.delete(team)
            removedIds.append(team.idUser)
            continue
        else:
            goodIds.append(team.idUser)
        ids.remove(team.idUser)
    
    if not goodIds and not ids and not removedIds:
        return send_response(400, 43070, {"message": "Nothing updated"}, "error")

    db.session.commit()

    return send_response(200, 43081, {"message": "user_teams changed", "badIds":badIds, "goodIds":goodIds, "removedIds":removedIds}, "success")

#TODO:Opravit
@user_team_bp.route("/user_team/get/idUser/idTask", methods = ["GET"])
@flask_login.login_required
def get_by_idUser_and_idTask():
    idUser = request.args.get("idUser", None)
    idTask = request.args.get("idTask", None)

    if not idTask:
        return send_response(400, 45010, {"message": "idTask not entered"}, "error")
    if not idUser:
        return send_response(400, 45020, {"message": "idUser not entered"}, "error")
    
    user_team = User_Team.query.filter_by(idUser = idUser, idTask = idTask).first()
    team = Team.query.filter_by(idTeam = user_team.idTeam, idTask = idTask).first()
    user = User.query.filter_by(id = idUser).first()
    task = Task.query.filter_by(id = idTask).first()
    version = Version_Team.query.filter_by(idTask=idTask, idTeam = user_team.idTeam).order_by(Version_Team.idVersion.desc()).first()
    
    if not user:
        return send_response(400, 45030, {"message": "Nonexistent user"}, "error")
    if not task:
        return send_response(400, 45040, {"message": "Nonexistent task"}, "error")
    if not user_team:
        return send_response(400, 45050, {"message": "Nonexistent user_team"}, "error")
    
    if not version:
        elaboration = None
    else:
        elaboration = version.elaboration
    
    guarantor = User.query.filter_by(id = task.guarantor).first()
    team_member = {"id": user.id, 
                    "name": user.name, 
                    "surname": user.surname, 
                    "abbreviation": user.abbreviation, 
                    "role": user.role.value, 
                    "profilePicture": user.profilePicture, 
                    "email": user.email, 
                    "idClass": all_user_classes(user.id),
                    "createdAt":user.createdAt,
                    "updatedAt":user.updatedAt
                }
    
    team = {"idTeam":team.idTeam,
            "status":team.status.value,
            "elaboration":elaboration, 
            "review":team.review, 
            "name":team.name, 
            "points":team.points, 
            }

    tasks = {"task":task.task,
            "name":task.name, 
            "statDate":task.startDate, 
            "endDate":task.endDate, 
            "type":task.type.value,
            "guarantor":{"id": guarantor.id, 
                        "name": guarantor.name, 
                        "surname": guarantor.surname, 
                        "abbreviation": guarantor.abbreviation, 
                        "role": guarantor.role.value, 
                        "profilePicture": guarantor.profilePicture, 
                        "email": guarantor.email, 
                        "idClass": all_user_classes(guarantor.id), 
                        "createdAt":guarantor.createdAt,
                        "updatedAt":guarantor.updatedAt
                        },
            "idTask":task.id,
            "taskPoints":task.points,
            "team":team,
            "teamMember":team_member
            }
    
    return send_response(200, 45061, {"message": "user_team for this task and user", "task": tasks}, "success")

@user_team_bp.route("/user_team/count/approved_without_review", methods=["GET"])
@flask_login.login_required
def count_approved_without_review():
    count = 0
    user_team = User_Team.query.filter_by(idUser = flask_login.current_user.id)

    for team in user_team:
        if Team.query.filter_by(idTeam = team.idTeam, idTask = team.idTask).review == None:
            count += 1

    return send_response(200, 47011, {"message": "Count of approved user_teams without review", "count": count}, "success")