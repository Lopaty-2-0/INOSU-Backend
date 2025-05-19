from flask import request, Blueprint
import flask_login
from src.utils.response import sendResponse
from src.utils.checkFileSize import checkFileSize
from src.utils.task import taskSaveSftp, taskDeleteSftp
from src.models.User import User
from src.models.Task import Task
from src.models.Task_Class import Task_Class
from src.models.User_Task import User_Task
from datetime import datetime
from app import db

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
    needApprove = bool(request.form.get("approve", None))
    lastTask = Task.query.order_by(Task.id.desc()).first()

    if lastTask:
        id = lastTask.id + 1
    else:
        id = 1

    if not taskName:
        return sendResponse(400, 26020, {"message": "Name not entered"}, "error")
    if not startDate:
        startDate = datetime.now()
    else:
        startDate = datetime.fromtimestamp(int(startDate)/1000000)
    if not endDate:
        return sendResponse(400, 26030, {"message": "endDate  not entered"}, "error")
    try:
        endDate = datetime.fromtimestamp(int(endDate)/1000000)
    except:
        return sendResponse(400, 26040, {"message":"End date not integer or is too far"}, "error")
    if endDate <= startDate:
        return sendResponse(400, 26050, {"message":"Ending before begining"}, "error")
    if not task:
        return sendResponse(400, 26060, {"message": "Task not entered"}, "error")
    if not task.filename.rsplit(".", 1)[1].lower() in task_extensions:
        return sendResponse(400, 26070, {"message": "Wrong file format"}, "error")
    if not needApprove:
        return sendResponse(400, 26080, {"message":"Approve not entered"}, "error")
    
    user = flask_login.current_user
    taskFileName = await taskSaveSftp(task_path, task, id)
    newTask = Task(name=taskName, startDate=startDate, endDate=endDate,guarantor=user.id, task=taskFileName, approve = needApprove)
    guarantor = {"id":user.id, "name":user.name, "surname": user.surname, "abbreviation": user.abbreviation, "createdAt": user.createdAt, "role": user.role, "profilePicture":user.profilePicture, "email":user.email}
        
    db.session.add(newTask)
    db.session.commit()

    return sendResponse(201, 26091, {"message":"Task created successfuly", "task":{"id": newTask.id, "name": task.name, "startDate": newTask.startDate, "endDate": newTask.endDate, "task": newTask.task, "guarantor": guarantor}}, "success")

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

#NOT WORKING
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
