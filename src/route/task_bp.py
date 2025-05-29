from flask import request, Blueprint
import flask_login
from src.utils.response import sendResponse
from src.utils.checkFileSize import checkFileSize
from src.utils.task import taskSaveSftp, taskDeleteSftp
from src.utils.sftp_utils import sftp_stat_async
from src.utils.allUserClasses import allUserClasses
from src.models.User import User
from src.models.Task import Task
from src.models.Task_Class import Task_Class
from src.models.User_Task import User_Task
from datetime import datetime
from app import db, ssh

task_bp = Blueprint("task", __name__)
task_extensions = ["pdf", "docx", "odt", "html", "zip"]
task_path = "/home/filemanager/files/tasks/"

@flask_login.login_required
@checkFileSize(32*1024*1024)
@task_bp.route("/task/add", methods = ["POST"])
async def taskAdd():
    if flask_login.current_user.role == "student":
        return sendResponse(403, 26010, {"message":"Students can not make tasks"}, "error")
    
    taskName = request.form.get("name", None)
    startDate = request.form.get("startDate", None)
    endDate = request.form.get("endDate", None)
    task = request.files.get("task", None)
    guarantor = request.form.get("guarantor", None)
    approve = request.form.get("approve", None)
    lastTask = Task.query.order_by(Task.id.desc()).first()

    if lastTask:
        id = lastTask.id + 1
    else:
        id = 1

    if not approve:
        return sendResponse(400, 26080, {"message":"Approve not entered"}, "error")
    
    needApprove = str(approve).lower() == "true"

    if not taskName:
        return sendResponse(400, 26020, {"message": "Name not entered"}, "error")
    if not startDate:
        startDate = datetime.now()
    else:
        startDate = datetime.fromtimestamp(int(startDate)/1000)
    if not endDate:
        return sendResponse(400, 26030, {"message": "endDate  not entered"}, "error")
    try:
        endDate = datetime.fromtimestamp(int(endDate)/1000)
    except:
        return sendResponse(400, 26040, {"message":"End date not integer or is too far"}, "error")
    if endDate <= startDate:
        return sendResponse(400, 26050, {"message":"Ending before begining"}, "error")
    if not task:
        return sendResponse(400, 26060, {"message": "Task not entered"}, "error")
    if not task.filename.rsplit(".", 1)[1].lower() in task_extensions:
        return sendResponse(400, 26070, {"message": "Wrong file format"}, "error")
    
    user = flask_login.current_user

    if await sftp_stat_async(ssh, task_path + str(id)):
        await taskDeleteSftp(task_path, id)
        
    taskFileName = await taskSaveSftp(task_path, task, id)
    newTask = Task(name=taskName, startDate=startDate, endDate=endDate,guarantor=user.id, task=taskFileName, approve = needApprove)
    guarantor = {"id":user.id, "name":user.name, "surname": user.surname, "abbreviation": user.abbreviation, "createdAt": user.createdAt, "role": user.role, "profilePicture":user.profilePicture, "email":user.email}
        
    db.session.add(newTask)
    db.session.commit()

    return sendResponse(201, 26091, {"message":"Task created successfuly", "task":{"id": newTask.id, "name": task.name, "startDate": newTask.startDate, "endDate": newTask.endDate, "task": newTask.task, "guarantor": guarantor}}, "success")

@task_bp.route("/task/get/guarantor", methods=["GET"])
@flask_login.login_required
def getTasksByGuarantor():
    idUser = request.args.get("idUser", None)
    tasks = Task.query.filter_by(guarantor=idUser).all()
    all_tasks = []

    if not idUser:
        return sendResponse(400, 29010, {"message": "No idUser entered"}, "error")

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
        
    return sendResponse(200, 29021, {"message": "Found tasks for guarantor", "tasks": all_tasks}, "success")

@task_bp.route("/task/get/id", methods=["GET"]) 
@flask_login.login_required
def getTaskById():
    idTask = request.args.get("idTask", None)
    task = Task.query.filter_by(id=idTask).first()

    if not idTask:
        return sendResponse(400, 30010, {"message": "No id entered"}, "error")

    if not task:
        return sendResponse(404, 30020, {"message": "Task not found"}, "error")

    task_data = {
        "id": task.id,
        "name": task.name,
        "startDate": task.startDate,
        "endDate": task.endDate,
        "task": task.task,
        "guarantor": task.guarantor,
        "approve": task.approve
    }

    return sendResponse(200, 30031, {"message": "Task found", "task": task_data}, "success")

@flask_login.login_required
@task_bp.route("/task/get", methods=["GET"])
def getAllTasks():
    all_tasks = []
    tasks = Task.query.all()

    for task in tasks:
        user = User.query.filter_by(id = task.guarantor).first()
        guarantor = {"id":user.id, "name":user.name, "surname": user.surname, "abbreviation": user.abbreviation, "createdAt": user.createdAt, "role": user.role, "profilePicture":user.profilePicture, "email":user.email}
        all_tasks.append({"id": task.id, "name": task.name, "startDate": task.startDate, "endDate": task.endDate, "task": task.task, "guarantor": guarantor})

    return sendResponse(200, 27011, {"message":"Found tasks", "tasks":all_tasks}, "success")

@task_bp.route("/task/delete", methods=["DELETE"])
@flask_login.login_required
async def taskDelete():
    data = request.get_json(force=True)
    id = data.get("id", None)

    if flask_login.current_user.role == "student":
        return sendResponse(403, 28010, {"message":"Students can not make tasks"}, "error")
    

    if not id:
        return sendResponse(400, 28020, {"message":"No id entered"}, "error")
    
    task_class = Task_Class.query.filter_by(idTask = id)
    user_task = User_Task.query.filter_by(idTask = id)

    if flask_login.current_user.id != Task.query.filter_by(id = id).first().guarantor or flask_login.current_user.role != "admin":
        return sendResponse(403, 28030, {"message":"No permission for that"}, "error")

    for user in user_task:
        db.session.delete(user)
    for cl in task_class:
        db.session.delete(cl)

    task = Task.query.filter_by(id=id).first()

    if not task:
        return sendResponse(400, 28040, {"message":"No task found"}, "error")
    
    db.session.delete(task)
    await taskDeleteSftp(task_path, task.id)
    db.session.commit()

    return sendResponse(200, 28051, {"message":"Task deleted"}, "success")

@task_bp.route("/task/get/possible", methods = ["GET"])
@flask_login.login_required
def getAllPossibleTask():
    tasks = Task.query.all()
    possibleTasks = []
    ids = allUserClasses(flask_login.current_user.id)

    for task in tasks:
        task_class = Task_Class.query.filter_by(idTask = task.id)
        user_task = User_Task.query.filter_by(idTask = task.id, idUser = flask_login.current_user.id).first()

        if user_task and user_task.status != "waiting":
            continue

        if task_class:
            for t in task_class:
                if t.idClass in ids:
                    user = User.query.filter_by(id = task.guarantor).first()
                    guarantor = {"id":user.id, "name":user.name, "surname": user.surname, "abbreviation": user.abbreviation, "createdAt": user.createdAt, "role": user.role, "profilePicture":user.profilePicture, "email":user.email}
                    possibleTasks.append({"id": task.id, "name": task.name, "startDate": task.startDate, "endDate": task.endDate, "task": task.task, "guarantor": guarantor})
                    break
        else:
            user = User.query.filter_by(id = task.guarantor).first()
            guarantor = {"id":user.id, "name":user.name, "surname": user.surname, "abbreviation": user.abbreviation, "createdAt": user.createdAt, "role": user.role, "profilePicture":user.profilePicture, "email":user.email}
            possibleTasks.append({"id": task.id, "name": task.name, "startDate": task.startDate, "endDate": task.endDate, "task": task.task, "guarantor": guarantor})

    return sendResponse(200, 46011, {"message":"All possible tasks for a user", "possibleTasks":possibleTasks}, "success")