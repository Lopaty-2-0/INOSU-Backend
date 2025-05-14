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
    badIds = []
    goodIds = []

    if not idTask:
        return sendResponse(400, 26010, {"message": "idTask not entered"}, "error")
    if not idClass:
        return sendResponse(400, 26010, {"message": "idClass not entered"}, "error")
    if not Task.query.filter_by(id=idTask).first():
        return sendResponse(400, 26010, {"message": "Nonexistent task"}, "error")
    
    for id in idClass:
        if not Class.query.filter_by(id=id).first():
            badIds.append(id)
        else:
            newMichal = Task_Class(idTask=idTask, idClass=id)
            db.session.add(newMichal)
            goodIds.append(id)

    db.session.commit()

    return sendResponse(200, 26010, {"message": "Task_class created successfuly", "badIds":badIds, "goodIds":goodIds}, "success")

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
    if not Task.query.filter_by(id=idTask).first():
        return sendResponse(400, 26010, {"message": "Nonexistent task"}, "error")
    if not Class.query.filter_by(id=idClass).first():
        return sendResponse(400, 26010, {"message": "Nonexistent class"}, "error")
    
    task_class = Task_Class.query.filter_by(idTask = idTask, idClass = idClass).first()

    if not task_class:
        return sendResponse(400, 26010, {"message": "Nonexistent task_class"}, "error")

    db.session.delete(task_class)
    db.session.commit()

    return sendResponse(200, 26010, {"message": "Task_class deleted successfuly"}, "success")

@task_class_bp.route("/task_class/update", methods=["PUT"])
@flask_login.login_required
def task_classUpdate():
    data = request.get_json(force=True)
    idTask = data.get("idTask", None)
    idClass = data.get("idClass", None)
    goodIds = []
    badIds = []

    if not idTask:
        return sendResponse(400, 26010, {"message": "idTask not entered"}, "error")
    if not idClass:
        return sendResponse(400, 26010, {"message": "idClass not entered"}, "error")
    if not Task.query.filter_by(id=idTask).first():
        return sendResponse(400, 26010, {"message": "Nonexistent task"}, "error")
    
    task_class = Task_Class.query.filter_by(idTask = idTask)

    if task_class:
        for task in task_class:
            db.session.delete(task)
    
    for id in idClass:
        if not Class.query.filter_by(id=id).first():
            badIds.append(id)
        else:
            newMichal = Task_Class(idTask=idTask, idClass=id)
            db.session.add(newMichal)
            goodIds.append(id)

    db.session.commit()

    return sendResponse(200, 26010, {"message": "Task_class updated", "badIds":badIds, "goodIds":goodIds}, "success")