from flask import request, Blueprint
import flask_login
from src.utils.response import send_response
from src.utils.check_file import check_file_size
from src.utils.task import task_save_sftp, task_delete_sftp
from src.utils.sftp_utils import sftp_stat_async
from src.utils.all_user_classes import all_user_classes
from src.models.User import User
from src.models.Task import Task
from src.models.Task_Class import Task_Class
from src.models.User_Task import User_Task
from datetime import datetime
from app import db, ssh, task_path

task_bp = Blueprint("task", __name__)
task_extensions = ["pdf", "docx", "odt", "html", "zip"]

@flask_login.login_required
@check_file_size(32*1024*1024)
@task_bp.route("/task/add", methods = ["POST"])
async def taskAdd():
    if flask_login.current_user.role == "student":
        return send_response(403, 26010, {"message":"Students can not make tasks"}, "error")
    
    taskName = request.form.get("name", None)
    startDate = request.form.get("startDate", None)
    endDate = request.form.get("endDate", None)
    task = request.files.get("task", None)
    guarantor = request.form.get("guarantor", None)
    approve = request.form.get("approve", None)

    if not approve:
        return send_response(400, 26080, {"message":"Approve not entered"}, "error")
    
    needApprove = str(approve).lower() == "true"

    if taskName:
        if len(taskName) > 255:
            taskName = None
    if not taskName:
        return send_response(400, 26020, {"message": "Name not entered"}, "error")
    if not startDate:
        startDate = datetime.now()
    else:
        startDate = datetime.fromtimestamp(int(startDate)/1000)
    if not endDate:
        return send_response(400, 26030, {"message": "endDate  not entered"}, "error")
    try:
        endDate = datetime.fromtimestamp(int(endDate)/1000)
    except:
        return send_response(400, 26040, {"message":"End date not integer or is too far"}, "error")
    if endDate <= startDate:
        return send_response(400, 26050, {"message":"Ending before begining"}, "error")
    if not task:
        return send_response(400, 26060, {"message": "Task not entered"}, "error")
    if not task.filename.rsplit(".", 1)[1].lower() in task_extensions or len(task.filename) > 255:
        return send_response(400, 26070, {"message": "Wrong file format or too long"}, "error")
    
    user = flask_login.current_user
    newTask = Task(name=taskName, startDate=startDate, endDate=endDate,guarantor=user.id, task = task.filename, approve = needApprove)
    db.session.add(newTask)
    id = Task.query.order_by(Task.id.desc()).first().id

    if await sftp_stat_async(ssh, task_path + str(id)):
        await task_delete_sftp(task_path, id)
        
    await task_save_sftp(task_path, task, id)

    db.session.commit()

    guarantor = {"id":user.id, "name":user.name, "surname": user.surname, "abbreviation": user.abbreviation, "createdAt": user.createdAt, "role": user.role, "profilePicture":user.profilePicture, "email":user.email}

    return send_response(201, 26091, {"message":"Task created successfuly", "task":{"id": newTask.id, "name": task.name, "startDate": newTask.startDate, "endDate": newTask.endDate, "task": newTask.task, "guarantor": guarantor}}, "success")

@task_bp.route("/task/get/guarantor", methods=["GET"])
@flask_login.login_required
def getTasksByGuarantor():
    idUser = request.args.get("idUser", None)
    tasks = Task.query.filter_by(guarantor=idUser).all()
    all_tasks = []

    if not idUser:
        return send_response(400, 29010, {"message": "No idUser entered"}, "error")

    for task in tasks:
        all_tasks.append({
            "id": task.id,
            "name": task.name,
            "startDate": task.startDate,
            "endDate": task.endDate,
            "task": task.task,
            "guarantor": task.guarantor,
            "approve": task.approve
        })
        
    return send_response(200, 29021, {"message": "Found tasks for guarantor", "tasks": all_tasks}, "success")

@task_bp.route("/task/get/id", methods=["GET"]) 
@flask_login.login_required
def getTaskById():
    idTask = request.args.get("idTask", None)
    task = Task.query.filter_by(id=idTask).first()

    if not idTask:
        return send_response(400, 30010, {"message": "No id entered"}, "error")

    if not task:
        return send_response(404, 30020, {"message": "Task not found"}, "error")

    task_data = {
        "id": task.id,
        "name": task.name,
        "startDate": task.startDate,
        "endDate": task.endDate,
        "task": task.task,
        "guarantor": task.guarantor,
        "approve": task.approve
    }

    return send_response(200, 30031, {"message": "Task found", "task": task_data}, "success")

@flask_login.login_required
@task_bp.route("/task/get", methods=["GET"])
def getAllTasks():
    all_tasks = []
    tasks = Task.query.all()

    for task in tasks:
        user = User.query.filter_by(id = task.guarantor).first()
        guarantor = {"id":user.id, "name":user.name, "surname": user.surname, "abbreviation": user.abbreviation, "createdAt": user.createdAt, "role": user.role, "profilePicture":user.profilePicture, "email":user.email, "updatedAt":user.updatedAt}
        all_tasks.append({"id": task.id, "name": task.name, "startDate": task.startDate, "endDate": task.endDate, "task": task.task, "guarantor": guarantor})

    return send_response(200, 27011, {"message":"Found tasks", "tasks":all_tasks}, "success")

@task_bp.route("/task/delete", methods=["DELETE"])
@flask_login.login_required
async def taskDelete():
    data = request.get_json(force=True)
    id = data.get("id", None)

    if flask_login.current_user.role == "student":
        return send_response(403, 28010, {"message":"Students can not delete"}, "error")
    

    if not id:
        return send_response(400, 28020, {"message":"No id entered"}, "error")
    
    task_class = Task_Class.query.filter_by(idTask = id)
    user_task = User_Task.query.filter_by(idTask = id)

    if flask_login.current_user.id != Task.query.filter_by(id = id).first().guarantor:
        return send_response(403, 28030, {"message":"No permission for that"}, "error")
    
    for user in user_task:
        db.session.delete(user)
    for cl in task_class:
        db.session.delete(cl)

    task = Task.query.filter_by(id=id).first()

    if not task:
        return send_response(400, 28040, {"message":"No task found"}, "error")
    
    db.session.delete(task)
    await task_delete_sftp(task_path, task.id)
    db.session.commit()

    return send_response(200, 28051, {"message":"Task deleted"}, "success")

@task_bp.route("/task/get/possible", methods = ["GET"])
@flask_login.login_required
def getAllPossibleTask():
    tasks = Task.query.all()
    waitingTasks = []
    classTasks = []
    ids = all_user_classes(flask_login.current_user.id)

    for task in tasks:
        task_class = Task_Class.query.filter_by(idTask = task.id)
        user_task = User_Task.query.filter_by(idTask = task.id, idUser = flask_login.current_user.id).first()

        if task_class and not user_task:
            for t in task_class:
                if t.idClass in ids:
                    user = User.query.filter_by(id = task.guarantor).first()
                    guarantor = {"id":user.id, "name":user.name, "surname": user.surname, "abbreviation": user.abbreviation, "createdAt": user.createdAt, "role": user.role, "profilePicture":user.profilePicture, "email":user.email, "updatedAt":user.updatedAt}
                    classTasks.append({"id": task.id, "name": task.name, "startDate": task.startDate, "endDate": task.endDate, "task": task.task, "guarantor": guarantor})
                    break

        elif user_task.status == "waiting":
            user = User.query.filter_by(id = task.guarantor).first()
            guarantor = {"id":user.id, "name":user.name, "surname": user.surname, "abbreviation": user.abbreviation, "createdAt": user.createdAt, "role": user.role, "profilePicture":user.profilePicture, "email":user.email, "updatedAt":user.updatedAt}
            waitingTasks.append({"id": task.id, "name": task.name, "startDate": task.startDate, "endDate": task.endDate, "task": task.task, "guarantor": guarantor})

    return send_response(200, 46011, {"message":"All possible tasks for a user", "waitingTasks":waitingTasks, "classTasks":classTasks}, "success")