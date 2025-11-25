from flask import request, Blueprint
import flask_login
from src.utils.response import send_response
from src.utils.check_file import check_file_size
from src.utils.task import task_save_sftp, task_delete_sftp
from src.utils.sftp_utils import sftp_stat_async
from src.models.User import User
from src.models.Task import Task
from src.models.User_Team import User_Team
from src.models.Team import Team
from src.models.Version_Team import Version_Team
from src.utils.enums import Status, Type, Role
from datetime import datetime
from src.utils.paging import task_paging
from src.utils.team import make_team
from app import db, ssh, task_path

task_bp = Blueprint("task", __name__)
task_extensions = ["pdf", "docx", "odt", "html", "zip"]

@flask_login.login_required
@check_file_size(32*1024*1024)
@task_bp.route("/task/add", methods = ["POST"])
async def add():
    taskName = request.form.get("name", None)
    endDate = request.form.get("endDate", None)
    task = request.files.get("task", None)
    guarantor = request.form.get("guarantor", None)
    deadline = request.form.get("deadline", None)
    points = request.form.get("points", None)

    startDate = datetime.now()

    if taskName:
        if len(taskName) > 255:
            taskName = None
    if not taskName:
        return send_response(400, 26010, {"message": "Name not entered"}, "error")
    if not endDate:
        return send_response(400, 26020, {"message": "endDate  not entered"}, "error")
    try:
        endDate = datetime.fromtimestamp(int(endDate)/1000)
    except:
        return send_response(400, 26030, {"message":"End date not integer or is too far"}, "error")
    if endDate <= startDate:
        return send_response(400, 26040, {"message":"Ending before begining"}, "error")
    if not task:
        return send_response(400, 26050, {"message": "Task not entered"}, "error")
    if not task.filename.rsplit(".", 1)[1].lower() in task_extensions or len(task.filename) > 255:
        return send_response(400, 26060, {"message": "Wrong file format or too long"}, "error")
    if flask_login.current_user.role != Role.Student:
        type = Type.Task
        user = flask_login.current_user
    else:
        if not guarantor:
            return send_response(400, 26070, {"message": "Guarantor not entered"}, "error")
        if not User.query.filter_by(id = guarantor).first():
            return send_response(400, 26080, {"message": "Nonexistent user"}, "error")
        if User.query.filter_by(id = guarantor).first().role == Role.Student:
            return send_response(400, 26080, {"message": "User can not be guarantor"}, "error")
        
        type = Type.Maturita
        user = flask_login.current_user
    if deadline:
        try:
            deadline = datetime.fromtimestamp(int(deadline)/1000)

            if deadline < startDate:
                return send_response(400, 26090, {"message":"Deadline before startDate"}, "error")
            if deadline < endDate:
                return send_response(400, 26100, {"message":"Deadline before endDate"}, "error")
        except:
            return send_response(400, 26110, {"message":"Deadline not integer or is too far"}, "error")
    if points:
        try:
            points = float(points)
        except:
            return send_response(400, 26120, {"message":"Points are not float"}, "error")
    else:
        points = None

    newTask = Task(name=taskName, startDate=startDate, endDate=endDate,guarantor=user.id, task = task.filename, type = type, points = points, deadline = deadline)

    db.session.add(newTask)

    id = Task.query.order_by(Task.id.desc()).first().id

    if await sftp_stat_async(ssh, task_path + str(id)):
        await task_delete_sftp(id)
        
    await task_save_sftp(task, id)

    db.session.commit()

    if type == Type.Maturita:
        id = await make_team(newTask.id, Status.Pending)
        db.session.add(User_Team(flask_login.current_user.id, id, newTask.id))
        db.session.commit()

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

    return send_response(201, 26131, {"message":"Task created successfuly", "task":{"id": newTask.id, "name": task.name, "startDate": newTask.startDate, "endDate": newTask.endDate, "task": newTask.task, "guarantor": guarantor, "deadline": deadline, "points": points}}, "success")

@flask_login.login_required
@task_bp.route("/task/get/guarantor", methods=["GET"])
def get_by_guarantor():
    idUser = request.args.get("idUser", None)
    amountForPaging = request.args.get("amountForPaging", None)
    pageNumber = request.args.get("pageNumber", None)
    searchQuery = request.args.get("searchQuery", None)

    all_tasks = []

    if not amountForPaging:
        return send_response(400, 19010, {"message": "amountForPaging not entered"}, "error")

    try:
        amountForPaging = int(amountForPaging)
    except:
        return send_response(400, 19020, {"message": "amountForPaging not integer"}, "error")
    
    if amountForPaging < 1:
        return send_response(400, 19030, {"message": "amountForPaging smaller than 1"}, "error")
    
    if not pageNumber:
        return send_response(400, 19040, {"message": "pageNumber not entered"}, "error")
    
    try:
        pageNumber = int(pageNumber)
    except:
        return send_response(400, 19050, {"message": "pageNumber not integer"}, "error")
    
    pageNumber -= 1

    if pageNumber < 0:
        return send_response(400, 19060, {"message": "pageNumber must be bigger than 0"}, "error")
    
    if not idUser:
        return send_response(400, 19070, {"message": "No idUser entered"}, "error")

    if not searchQuery:
        tasks = Task.query.filter_by(guarantor = idUser).offset(amountForPaging * pageNumber).limit(amountForPaging)
        count = Task.query.filter_by(guarantor = idUser).count()
    else:
        tasks, count = task_paging(searchQuery = searchQuery, amountForPaging = amountForPaging, pageNumber = pageNumber, specialSearch = idUser, typeOfSpecialSearch = "guarantor")

    for task in tasks:
        all_tasks.append({
            "id": task.id,
            "name": task.name,
            "startDate": task.startDate,
            "endDate": task.endDate,
            "task": task.task,
            "guarantor": task.guarantor,
            "deadline": task.deadline,
            "points":task.points
        })
        
    return send_response(200, 19081, {"message": "Found tasks for guarantor", "tasks": all_tasks, "count": count}, "success")

@flask_login.login_required
@task_bp.route("/task/get/id", methods=["GET"]) 
def get_by_id():
    idTask = request.args.get("idTask", None)
    task = Task.query.filter_by(id=idTask).first()
    task_data = None

    if not idTask:
        return send_response(400, 30010, {"message": "No id entered"}, "error")

    if not task:
        return send_response(404, 30020, {"message": "Task not found"}, "error")

    user = User.query.filter_by(id = task.quarantor).first()
    guarantor = {"id":user.id, "name":user.name, "surname": user.surname, "abbreviation": user.abbreviation, "createdAt": user.createdAt, "role": user.role.value, "profilePicture":user.profilePicture, "email":user.email}

    task_data = {
        "id": task.id,
        "name": task.name,
        "startDate": task.startDate,
        "endDate": task.endDate,
        "task": task.task,
        "guarantor": guarantor,
        "points": task.points,
        "deadline": task.deadline
    }
    
    return send_response(200, 30031, {"message": "Task found", "task": task_data}, "success")

@flask_login.login_required
@task_bp.route("/task/get", methods=["GET"])
def get():
    amountForPaging = request.args.get("amountForPaging", None)
    pageNumber = request.args.get("pageNumber", None)
    searchQuery = request.args.get("searchQuery", None)

    all_tasks = []

    if not amountForPaging:
        return send_response(400, 27010, {"message": "amountForPaging not entered"}, "error")

    try:
        amountForPaging = int(amountForPaging)
    except:
        return send_response(400, 27020, {"message": "amountForPaging not integer"}, "error")
    
    if amountForPaging < 1:
        return send_response(400, 27030, {"message": "amountForPaging smaller than 1"}, "error")
    
    if not pageNumber:
        return send_response(400, 27040, {"message": "pageNumber not entered"}, "error")
    
    try:
        pageNumber = int(pageNumber)
    except:
        return send_response(400, 27050, {"message": "pageNumber not integer"}, "error")
    
    pageNumber -= 1

    if pageNumber < 0:
        return send_response(400, 27060, {"message": "pageNumber must be bigger than 0"}, "error")

    if not searchQuery:
        tasks = Task.query.offset(amountForPaging * pageNumber).limit(amountForPaging)
        count = Task.query.count()
    else:
        tasks, count = task_paging(searchQuery = searchQuery, amountForPaging = amountForPaging, pageNumber = pageNumber)


    for task in tasks:
        user = User.query.filter_by(id = task.guarantor).first()
        guarantor = {"id":user.id, "name":user.name, "surname": user.surname, "abbreviation": user.abbreviation, "createdAt": user.createdAt, "role": user.role.value, "profilePicture":user.profilePicture, "email":user.email, "updatedAt":user.updatedAt}
        all_tasks.append({"id": task.id, "name": task.name, "startDate": task.startDate, "endDate": task.endDate, "task": task.task, "guarantor": guarantor, "deadline": task.deadline, "points": task.points})

    return send_response(200, 27071, {"message":"Found tasks", "tasks":all_tasks, "count":count}, "success")

@flask_login.login_required
@task_bp.route("/task/delete", methods=["DELETE"])
async def delete():
    data = request.get_json(force=True)
    id = data.get("id", None)

    if flask_login.current_user.role == Role.Student:
        return send_response(403, 28010, {"message":"Students can not delete"}, "error")

    if not id:
        return send_response(400, 28020, {"message":"No id entered"}, "error")
    
    teams = Team.query.filter_by(idTask = id)
    user_team = User_Team.query.filter_by(idTask = id)

    task = Task.query.filter_by(id=id).first()

    if not task:
        return send_response(400, 28030, {"message":"No task found"}, "error")

    if flask_login.current_user.id != task.guarantor:
        return send_response(403, 28040, {"message":"No permission for that"}, "error")
    
    for user in user_team:
        db.session.delete(user)

    for team in teams:
        versions = Version_Team.query.filter_by(idTask = id, idTeam = team.idTeam)

        for ver in versions:
            db.session.delete(ver)

        db.session.delete(team)
    
    db.session.delete(task)
    await task_delete_sftp(task.id)
    db.session.commit()

    return send_response(200, 28051, {"message":"Task deleted"}, "success")

#TODO:nutno zjistit co dělá a pak ji upravit
"""@flask_login.login_required
@task_bp.route("/task/get/possible", methods = ["GET"])
def get_all_possible():
    tasks = Task.query.all()
    waitingTasks = []

    for task in tasks:
        user_team = User_Team.query.filter_by(idTask = task.id, idUser = flask_login.current_user.id).first()

        if not user_team:
            continue

        if Team.query.filter_by(idTask = task.id, idUser = flask_login.current_user.id).first().status == Status.Waiting:
            user = User.query.filter_by(id = task.guarantor).first()
            guarantor = {"id":user.id, "name":user.name, "surname": user.surname, "abbreviation": user.abbreviation, "createdAt": user.createdAt, "role": user.role.value, "profilePicture":user.profilePicture, "email":user.email, "updatedAt":user.updatedAt}
            waitingTasks.append({"id": task.id, "name": task.name, "startDate": task.startDate, "endDate": task.endDate, "task": task.task, "guarantor": guarantor})

    return send_response(200, 46011, {"message":"All possible tasks for a user", "waitingTasks":waitingTasks}, "success")"""