from flask import Blueprint
from src.models.Maturita import Maturita
from src.models.Maturita_Task import Maturita_Task
from src.models.Task import Task
from src.models.User_Team import User_Team
from src.models.User import User
from src.models.Topic import Topic
from src.models.Team import Team
import flask_login
import datetime
from src.utils.response import send_response
from app import max_INT
from flask import request
from src.utils.enums import Status

maturita_task_bp = Blueprint("maturita_task", __name__)

@flask_login.login_required
@maturita_task_bp.route("/maturita_task/get/table", methods = ["GET"])
def get_table():
    amountForPaging = request.args.get("amountForPaging", None)
    pageNumber = request.args.get("pageNumber", None)

    allTasks = []

    now = datetime.datetime.now(tz = datetime.timezone.utc)
    maturita = Maturita.query.filter(Maturita.startDate <= now, now <= Maturita.endDate).first()

    if not maturita:
        return send_response(400, 83010, {"message":"There is no current maturita"}, "error")
    if not amountForPaging:
        return send_response(400, 83020, {"message": "amountForPaging not entered"}, "error")

    try:
        amountForPaging = int(amountForPaging)
    except:
        return send_response(400, 83030, {"message": "amountForPaging not integer"}, "error")
    
    if amountForPaging < 1:
        return send_response(400, 83040, {"message": "amountForPaging smaller than 1"}, "error")
    
    if amountForPaging > max_INT:
        return send_response(400, 83050, {"message": "amountForPaging too big"}, "error")
    
    if not pageNumber:
        return send_response(400, 83060, {"message": "pageNumber not entered"}, "error")
    
    try:
        pageNumber = int(pageNumber)
    except:
        return send_response(400, 83070, {"message": "pageNumber not integer"}, "error")
    if pageNumber > max_INT + 1:
        return send_response(400, 83080, {"message": "pageNumber too big"}, "error")
    
    pageNumber -= 1

    if pageNumber < 0:
        return send_response(400, 83090, {"message": "pageNumber must be bigger than 0"}, "error")

    maturitaTask = Maturita_Task.query.join(Team, (Team.guarantor == Maturita_Task.guarantor) & (Team.idTask == Maturita_Task.idTask) & (Team.status == Status.Approved)).filter(Maturita_Task.idMaturita == maturita.id).offset(amountForPaging * pageNumber).limit(amountForPaging)
    count = Maturita_Task.query.filter(Maturita_Task.idMaturita == maturita.id).count()

    for taskMaturita in maturitaTask:
        task = Task.query.filter_by(id = taskMaturita.idTask, guarantor = taskMaturita.guarantor).first()
        guarantor = User.query.filter_by(id = taskMaturita.guarantor).first()
        userTeam = User_Team.query.filter_by(idTask = taskMaturita.idTask, guarantor = taskMaturita.guarantor).first()
        student = User.query.filter_by(id = userTeam.idUser).first()
        objector = User.query.filter_by(id = taskMaturita.guarantor).first()
        topic = Topic.query.filter_by(id = taskMaturita.idTopic).first()

        if not objector:
            objectorData = {}
        else:
            objectorData = {
                "id":objector.id,
                "name":objector.name,
                "surname": objector.surname,
                "abbreviation": objector.abbreviation,
                "createdAt": objector.createdAt,
                "role": objector.role.value,
                "profilePicture":objector.profilePicture,
                "email":objector.email
                }

        guarantorData = {
            "id":guarantor.id,
            "name":guarantor.name,
            "surname": guarantor.surname,
            "abbreviation": guarantor.abbreviation,
            "createdAt": guarantor.createdAt,
            "role": guarantor.role.value,
            "profilePicture":guarantor.profilePicture,
            "email":guarantor.email
            }

        allTasks.append({
            "user":{
                "id":student.id,
                "surname":student.surname,
                "name":student.name,
                "profilePicture":student.profilePicture,
                "email":student.email
            },
            "topic":{
                "id":topic.id,
                "name":topic.name,
            },
            "variant":taskMaturita.variant,
            "task":task.name,
            "guarantor":guarantorData,
            "objector":objectorData
        })

    return send_response(200, 83101, {"message":"All tasks for current maturita", "tasks":allTasks, "count":count}, "success")