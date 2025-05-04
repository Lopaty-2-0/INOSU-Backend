from flask import request, Blueprint
import flask_login
from src.utils.response import sendResponse
from src.utils.checkFileSize import checkFileSize
from src.utils.taskSave import taskSave
from src.models.User import User
from src.models.Task import Task
from datetime import datetime
from app import db

task_bp = Blueprint("task", __name__)
task_extensions = ["pdf", "docx", "odt", "html"]
task_path = "/home/filemanager/files/tasks/"

@flask_login.login_required
@checkFileSize(32*1024*1024)
@task_bp.route("/task/add", methods = ["POST"])
async def add():
    taskName = request.form.get("name", None)
    startDate = request.form.get("startDate", None)
    endDate = request.form.get("endDate", None)
    task = request.files.get("task", None)
    guarantor = request.form.get("guarantor", None)
    lastTask = Task.query.order_by(Task.id.desc()).first()
    if lastTask:
        id = lastTask.id + 1
    else:
        id = 1
    print(id)

    if not taskName:
        return sendResponse(400, 14010, {"message": "Name not entered"}, "error")
    if not endDate:
        return sendResponse(400, 14010, {"message": "endDate  not entered"}, "error")
    if not task:
        return sendResponse(400, 14010, {"message": "Task not entered"}, "error")
    if not task.filename.rsplit(".", 1)[1].lower() in task_extensions:
        return sendResponse(400, 1180, {"message": "Wrong file format"}, "error")
    if not guarantor:
        return sendResponse(400, 1, {"message":"Guarantor not entered"}, "error")
    if User.query.filter_by(id = guarantor).first():
        return sendResponse(400, 1, {"message":"Nonexistent user"}, "error")
    if not startDate:
        startDate = datetime.now()


    taskFileName = await taskSave(task_path, task)
    newTask = Task(name=taskName, startDate=startDate, endDate=endDate,guarantor=guarantor, task=taskFileName)

    db.session.add(newTask)
    db.session.commit()
