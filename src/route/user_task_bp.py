from flask import request, Blueprint
import flask_login
from app import db
from src.models.User_Task import User_Task
from src.models.Task import Task
from src.models.Task_Class import Task_Class
from src.models.User_Class import User_Class
from src.models.User import User
from src.utils.response import sendResponse

user_task_bp = Blueprint("user_task", __name__)

@user_task_bp.route("/user_task/add", methods=["POST"])
@flask_login.login_required
def task_classAdd():
    data = request.get_json(force=True)
    idTask = data.get("idTask", None)
    idUser = data.get("idUser", None)
    badIds = []
    goodIds = []

    if not idTask:
        return sendResponse(400, 26010, {"message": "idTask not entered"}, "error")
    if not idUser:
        return sendResponse(400, 26010, {"message": "idUser not entered"}, "error")
    if not Task.query.filter_by(id=idTask).first():
        return sendResponse(400, 26010, {"message": "Nonexistent task"}, "error")
    if not Task_Class.query.filter_by(idTask=idTask).first():
        return sendResponse(400, 26010, {"message": "This task isnt assigned to a class"}, "error")
    if Task.query.filter_by(id = idTask).first().approve:
        status = "pending"
    else:
        status = "approved"
    #udělej to ještě pro int
    tc = Task_Class.query.filter_by(idTask=idTask)
    for idU in idUser:
        if not User.query.filter_by(id=idU).first():
            badIds.append(idU)
            continue

        cl = User_Class.query.filter_by(idUser=idU)
        status = False

        for c in cl:
            for t in tc:
                if c.idClass == t.idClass:
                    newUser_Task = User_Task(idUser=idU, idTask=idTask, elaboration=None, review=None, status=status)
                    db.session.add(newUser_Task)
                    goodIds.append(idU)
                    status = True
                    break
        if not status:
            badIds.append(idU)

    db.session.commit()

    return sendResponse(200, 26010, {"message": "User_task created successfuly","badIds":badIds, "goodIds":goodIds}, "success")

@user_task_bp.route("/user_task/delete", methods=["DELETE"])
@flask_login.login_required
def task_classDelete():
    data = request.get_json(force=True)
    idTask = data.get("idTask", None)
    idUser = data.get("idUser", None)

    if not idTask:
        return sendResponse(400, 26010, {"message": "idTask not entered"}, "error")
    if not idUser:
        return sendResponse(400, 26010, {"message": "idUser not entered"}, "error")
    
    user_task = User_Task.query.filter_by(idTask = idTask, idUser = idUser).first()

    if not user_task:
        return sendResponse(400, 26010, {"message": "Nonexistent task"}, "error")

    db.session.delete(user_task)
    db.session.commit()

    return sendResponse(200, 26010, {"message": "User_task deleted successfuly"}, "success")