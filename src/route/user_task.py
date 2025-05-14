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

@user_task_bp.route("/task_class/add", methods=["POST"])
@flask_login.login_required
def task_classAdd():
    data = request.get_json(force=True)
    idTask = data.get("idTask", None)
    idUser = data.get("idUser", None)

    if not idTask:
        return sendResponse(400, 26010, {"message": "idTask not entered"}, "error")
    if not idUser:
        return sendResponse(400, 26010, {"message": "idUser not entered"}, "error")
    if not Task.query.filter_by(id=idTask).first():
        return sendResponse(400, 26010, {"message": "Nonexistent task"}, "error")
    if not User.query.filter_by(id=idUser).first():
        return sendResponse(400, 26010, {"message": "Nonexistent user"}, "error")
    if User_Class.query.filter_by(id=idUser).first().idClass != Task_Class.query.filter_by(id=idTask).first().idClass:
        return sendResponse(400, 26010, {"message": "Task not for this users class"}, "error")
    if Task.query.filter_by(id = idTask).first().approve:
        status = "pending"
    else:
        status = "approved"
    
    newUser_Task = User_Task(idUser=idUser, idTask=idTask, elaboration=None, review=None, status=status)
    db.session.add(newUser_Task)
    db.session.commit()

    return sendResponse(200, 26010, {"message": "Task_class created successfuly","user_task":{ "idTask": newUser_Task.idTask, "idUser":newUser_Task.idUser, "elaboration": newUser_Task.elaboration, "review": newUser_Task.review, "status":newUser_Task.status}}, "success")

@user_task_bp.route("/task_class/delete", methods=["DELETE"])
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