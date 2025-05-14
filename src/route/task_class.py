from flask import request, Blueprint
import flask_login
from app import db
from src.models.Task_Class import Task_Class
from src.models.Task import Task
from src.models.Class import Class
from src.utils.response import sendResponse

task_class_bp = Blueprint("task_class", __name__)

@task_class_bp.route("/task_class/add", methods=["POST"])
@flask_login.login_required
def task_classAdd():
    data = request.get_json(force=True)
    idTask = data.get("idTask", None)
    idClass = data.get("idClass", None)

    if not idTask:
        return sendResponse(400, 26010, {"message": "idTask not entered"}, "error")
    if not idClass:
        return sendResponse(400, 26010, {"message": "idClass not entered"}, "error")
    if not Task.query.filter_by(id=idTask).first():
        return sendResponse(400, 26010, {"message": "Nonexistent task"}, "error")
    if not Class.query.filter_by(id=idClass).first():
        return sendResponse(400, 26010, {"message": "Nonexistent class"}, "error")
    
    newTask_class = Task_Class(idTask=idTask, idClass=idClass)

    db.session.add(newTask_class)
    db.session.commit()

    return sendResponse(200, 26010, {"message": "Task_class created successfuly","task_class":{ "idTask": newTask_class.idTask, "idClass":newTask_class.idClass}}, "success")

@task_class_bp.route("/task_class/delete", methods=["DELETE"])
@flask_login.login_required
def task_classDelete():
    data = request.get_json(force=True)
    idTask = data.get("idTask", None)
    idClass = data.get("idClass", None)

    if not idTask:
        return sendResponse(400, 26010, {"message": "idTask not entered"}, "error")
    if not idClass:
        return sendResponse(400, 26010, {"message": "idClass not entered"}, "error")
    
    task_class = Task_Class.query.filter_by(idTask = idTask, idClass = idClass).first()

    if not task_class:
        return sendResponse(400, 26010, {"message": "Nonexistent task_class"}, "error")

    db.session.delete(task_class)
    db.session.commit()

    return sendResponse(200, 26010, {"message": "Task_class deleted successfuly"}, "success")
