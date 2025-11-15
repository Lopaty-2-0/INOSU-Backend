from flask import request, Blueprint
import flask_login
from app import db
from src.models.Team import Team
from src.models.User import User
from src.models.Task import Task
from src.models.User_Team import User_Team
from src.models.Version_Team import Version_Team
from src.utils.team import team_delete
from src.utils.response import send_response
from src.utils.team import make_team
from src.utils.enums import Status
import json
from src.utils.all_user_classes import all_user_classes
from urllib.parse import unquote

team_bp = Blueprint("team", __name__)
task_extensions = ["pdf", "docx", "odt", "html", "zip"]

@team_bp.route("/team/add", methods=["POST"])
@flask_login.login_required
async def add():
    data = request.get_json(force=True)
    idTask = data.get("idTask", None)
    name = data.get("name", None)

    if not idTask:
        return send_response(400, 30010, {"message": "IdTask not entered"}, "error")
    
    task = Task.query.filter_by(id = idTask).first()

    if not task:
        return send_response(400, 30020, {"message": "Nonexistent task"}, "error")
    if not flask_login.current_user.id == task.guarantor:
        return send_response(400, 30030, {"message": "User is not guarantor"}, "error")
    if Team.query.filter_by(idTask = idTask, name = name).first():
        return send_response(400, 30030, {"message": "Team with this name already exists"}, "error")
    
    await make_team(idTask = idTask, status = Status.Approved, name = name)
    
    return send_response(201, 30041, {"message": "Team created successfuly"}, "success")

@team_bp.route("/team/delete", methods=["DELETE"])
@flask_login.login_required
async def delete():
    data = request.get_json(force=True)
    idTask = data.get("idTask", None)
    idTeam = data.get("idTeam", None)

    if not idTask:
        return send_response(400, 31010, {"message": "IdTask not entered"}, "error")
    if not idTeam:
        return send_response(400, 31020, {"message": "IdTeam not entered"}, "error")
    if not Task.query.filter_by(id = idTask).first():
        return send_response(400, 31030, {"message": "Nonexistent task"}, "error")
    if not Team.query.filter_by(idTeam = idTeam, idTask = idTask).first():
        return send_response(400, 31040, {"message": "Nonexistent team"}, "error")
    if Task.query.filter_by(id = idTask).first().guarantor != flask_login.current_user.id:
        return send_response(400, 31050, {"message": "User is not guarantor"}, "error")
    
    users = User_Team.query.filter_by(idTask = idTask, idTeam = idTeam)
    team = Team.query.filter_by(idTeam = idTeam, idTask = idTask).first()
    versions = Version_Team.query.filter_by(idTeam = idTeam, idTask = idTask)

    for user in users:
        db.session.delete(user)
    
    for version in versions:
        db.session.delete(version)

    await team_delete(idTeam = idTeam, idTask = idTask)
    db.session.delete(team)
    db.session.commit()

    return send_response(200, 31061, {"message": "team deleted successfuly"}, "success")

@team_bp.route("/team/update", methods=["PUT"])
@flask_login.login_required
async def update():
    data = request.get_json(force = True)
    idTask = data.get("idTask", None)
    idTeam = data.get("idTeam", None)
    status = data.get("status", None)
    review = data.get("review", None)
    points = data.get("points", None)
    ids = []

    if not idTask:
        return send_response(400, 32010, {"message": "IdTask not entered"}, "error")
    if not idTeam:
        return send_response(400, 32020, {"message": "IdTeam not entered"}, "error")
    
    task = Task.query.filter_by(id = idTask).first()

    if not task:
        return send_response(400, 32030, {"message": "Nonexistent task"}, "error")
    
    team = Team.query.filter_by(idTeam = idTeam, idTask = idTask).first()

    if not team:
        return send_response(400, 32040, {"message": "Nonexistent team"}, "error")
    if not flask_login.current_user.id == task.guarantor:
        return send_response(400, 32050, {"message": "User doesnt have rights"}, "error")
    if not review and not status and not points and status != Status.Pending.value:
        return send_response(400, 32060, {"message": "Nothing not entered to change"}, "error")
    if status not in [s.value for s in Status]:
        return send_response(400, 32070, {"message": "Status not our type"}, "error")
    elif status != Status.Pending.value:
        team.status = Status(status)
    try:
        points = float(points)
    except:
        return send_response(400, 32080, {"message": "Points are not integer or float"}, "error")
    
    team.review = review
    
    db.session.commit()

    return send_response(200, 32091, {"message": "team updated"}, "success")

#TODO:předělat na to query
@flask_login.login_required
@team_bp.route("/team/get", methods=["GET"])
def get_by_task():
    idTask = request.args.get("idTask", None)
    amountForPaging = request.args.get("amountForPaging", None)
    pageNumber = request.args.get("pageNumber", None)

    if not amountForPaging:
        return send_response(400, 41010, {"message": "amountForPaging not entered"}, "error")
    
    try:
        amountForPaging = int(amountForPaging)
    except:
        return send_response(400, 41020, {"message": "amountForPaging not integer"}, "error")
    
    if amountForPaging < 1:
        return send_response(400, 41030, {"message": "amountForPaging smaller than 1"}, "error")
    
    if not pageNumber:
        return send_response(400, 41040, {"message": "pageNumber not entered"}, "error")
    
    try:
        pageNumber = int(pageNumber)
    except:
        return send_response(400, 41050, {"message": "pageNumber not integer"}, "error")
    
    pageNumber -= 1

    if pageNumber < 0:
        return send_response(400, 41060, {"message": "pageNumber must be bigger than 0"}, "error")

    right_teams = []
    users = []

    if not idTask:
        return send_response(400, 41070, {"message": "idTask not entered"}, "error")
    if not Task.query.filter_by(id = idTask).first():
        return send_response(400, 41080, {"message": "Nonexistent task"}, "error")
    
    teams = Team.query.filter_by(idTask = idTask).offset(amountForPaging * pageNumber).limit(amountForPaging)

    if not teams:
        return send_response(400, 41090, {"message": "No team found"}, "error")
    
    count = teams.count()
    
    for team in teams:
        counts = User_Team.query.filter_by(idTask=idTask, idTeam=team.idTeam).count()
        
        if counts == 1:
            user = User.query.filter_by(id = User_Team.query.filter_by(idTask = idTask, idTeam = team.idTeam).first().idUser).first()
            users.append({
                        "idTeam":team.idTeam,
                        "name":team.name,
                        "status":team.status.value,
                        "elaboration":team.elaboration,
                        "review":team.review, 
                        "points":team.points,
                        "userData":{
                            "id":user.id,
                            "name":user.name,
                            "surname":user.surname,
                            "profilePicture":user.profilePicture
                        }
                        })

        right_teams.append({
                    "status":team.status.value,
                    "elaboration":team.elaboration,
                    "review":team.review, 
                    "idTeam":team.idTeam,
                    "count": count,
                    "name":team.name,
                    "points":team.points
                    })

    return send_response(200, 41101, {"message": "All teams for this task", "teams":right_teams, "users":users, "count": count}, "success")

#TODO: vymyslet lépe tento paging + předělat na query
@team_bp.route("/team/get/status/guarantor", methods=["GET"])
@flask_login.login_required
def get_by_status_guarantor():
    status = request.args.get("status", "")
    amountForPaging = request.args.get("amountForPaging", None)
    pageNumber = request.args.get("pageNumber", None)
    guarantorTasks = []
    teams = []
    count = 0
    goodStatuses = []
    
    if not amountForPaging:
        return send_response(400, 40010, {"message": "amountForPaging not entered"}, "error")
    
    try:
        amountForPaging = int(amountForPaging)
    except:
        return send_response(400, 40020, {"message": "amountForPaging not integer"}, "error")
    
    if amountForPaging < 1:
        return send_response(400, 40030, {"message": "amountForPaging smaller than 1"}, "error")
    
    if not pageNumber:
        return send_response(400, 40040, {"message": "pageNumber not entered"}, "error")
    
    try:
        pageNumber = int(pageNumber)
    except:
        return send_response(400, 40050, {"message": "pageNumber not integer"}, "error")
    
    pageNumber -= 1

    if pageNumber < 0:
        return send_response(400, 40060, {"message": "pageNumber must be bigger than 0"}, "error")
    
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
        tasks = Task.query.filter_by(guarantor = flask_login.current_user.id).offset(amountForPaging * pageNumber).limit(amountForPaging)
        for task in tasks:
            team = Team.query.filter_by(idTask = task.id, status = Status(s))

            for t in team:
                version = Version_Team.query.filter_by(idTask=t.idTask, idTeam = t.idTeam).order_by(Version_Team.idVersion.desc()).first()

                if not version:
                    elaboration = None
                else:
                    elaboration = version.elaboration
                teams.append({
                            "idTeam":t.idTeam,
                            "status":t.status.value,
                            "elaboration":elaboration, 
                            "review":t.review, 
                            "name":t.name, 
                            "points":t.points, 
                            })

            if teams:
                guarantorTasks.append({"teams":teams,
                            "task":task.task,
                            "name":task.name, 
                            "statDate":task.startDate, 
                            "endDate":task.endDate, 
                            "type":task.type.value,
                            "guarantor":{"id": flask_login.current_user.id, 
                                        "name": flask_login.current_user.name, 
                                        "surname": flask_login.current_user.surname, 
                                        "abbreviation": flask_login.current_user.abbreviation, 
                                        "role": flask_login.current_user.role.value, 
                                        "profilePicture": flask_login.current_user.profilePicture, 
                                        "email": flask_login.current_user.email, 
                                        "idClass": all_user_classes(flask_login.current_user.id), 
                                        "createdAt":flask_login.current_user.createdAt,
                                        "updatedAt":flask_login.current_user.updatedAt
                                        },
                            "idTask":task.id,
                            "taskPoints":task.points
                            })
                count += 1
                teams = []
    
    if not guarantorTasks:
        return send_response(400, 40070, {"message": "No guarantorTasks found"}, "error")
    
    return send_response(200, 40081, {"message": "All guarantor tasks with these statuses for current user", "guarantorTasks":guarantorTasks, "count": count}, "success")

#TODO: předělat na paging + předělat na query
@team_bp.route("/team/get/status/idTask", methods=["GET"])
@flask_login.login_required
def get_with_status_and_idTask():
    status = request.args.get("status", "")
    idTask = request.args.get("idTask", None)
    amountForPaging = request.args.get("amountForPaging", None)
    pageNumber = request.args.get("pageNumber", None)
    tasks = []
    right_teams = []
    goodStatuses = []

    if not amountForPaging:
        return send_response(400, 44010, {"message": "amountForPaging not entered"}, "error")
    
    try:
        amountForPaging = int(amountForPaging)
    except:
        return send_response(400, 44020, {"message": "amountForPaging not integer"}, "error")
    
    if amountForPaging < 1:
        return send_response(400, 44030, {"message": "amountForPaging smaller than 1"}, "error")
    
    if not pageNumber:
        return send_response(400, 44040, {"message": "pageNumber not entered"}, "error")
    
    try:
        pageNumber = int(pageNumber)
    except:
        return send_response(400, 44050, {"message": "pageNumber not integer"}, "error")
    
    pageNumber -= 1

    if pageNumber < 0:
        return send_response(400, 44060, {"message": "pageNumber must be bigger than 0"}, "error")
    
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
    
    if not idTask:
        return send_response(400, 44070, {"message": "idTask not entered"}, "error")
    if not Task.query.filter_by(id = idTask).first():
        return send_response(400, 44080, {"message": "Nonexistent task"}, "error")

    task = Task.query.filter_by(id = idTask).first()
    guarantor = User.query.filter_by(id = task.guarantor).first()

    if flask_login.current_user.id != task.guarantor:
        return send_response(403, 44090, {"message": "No permission"}, "error")

    for s in goodStatuses:
        teams = Team.query.filter_by(idTask = idTask, status = Status(s)).offset(amountForPaging * pageNumber).limit(amountForPaging)

        for team in teams:
            version = Version_Team.query.filter_by(idTask=team.idTask, idTeam = team.idTeam).order_by(Version_Team.idVersion.desc()).first()

            if not version:
                elaboration = None
            else:
                elaboration = version.elaboration

            right_teams.append({"idTeam":team.idTeam,
                                "status":team.status.value,
                                "elaboration":elaboration, 
                                "review":team.review, 
                                "name":team.name, 
                                "points":team.points, 
                                })
            
        tasks.append({"task":task.task,
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
                    "teams":right_teams
                    })
                
    return send_response(200, 44101, {"message": "All teams for this task and statuses", "tasks": tasks}, "success")