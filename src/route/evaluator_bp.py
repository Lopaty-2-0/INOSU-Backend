from flask import Blueprint
from src.models.Maturita import Maturita
from src.models.Maturita_Task import Maturita_Task
from src.models.Evaluator import Evaluator
from src.models.Task import Task
from src.models.Team import Team
from src.models.User_Team import User_Team
from src.models.Version_Team import Version_Team
from src.models.User import User
import flask_login
from src.utils.response import send_response
from src.utils.enums import Role
from app import db, maxINT
from flask import request

evaluator_bp = Blueprint("evaluator", __name__)

"""@evaluator_bp.route("/evaluator/update", methods = ["PuT"])
@flask_login.login_required
def add():
    if flask_login.current_user.role == Role.Student:
        return send_response(403, 67010, {"message": "No permission for that"}, "error")
    
    data = request.get_json(force=True)
    idUser = data.get("idUser", None)
    idMaturita = data.get("idMaturita", None)
    goodIds = []
    badIds = []


    if not idUser:
        return send_response(400, 67020, {"message": "grade missing"}, "error")
    if not idMaturita:
        return send_response(400, 67030, {"message": "maxPoints missing"}, "error")
    
    if not isinstance(idUser, list):
        idUser = [idUser]

    try:
        idMaturita = int(idMaturita)
    except:
        return send_response(400, 67030, {"message": "idMaturita is not int"}, "error")
    if idMaturita > maxINT or idMaturita <= 0:
        return send_response(400, 4060, {"message": "idMaturita not valid"}, "error")
    if not Maturita.query.filter_by(id = idMaturita).first():
        return send_response(400, 4060, {"message": "idMaturita not valid"}, "error")
    
    evaluators = Evaluator.query.filter_by(idMaturita = idMaturita)

    for evaluator in evaluators:
        db.session.delete(evaluator)
    
    db.session.commit()
    
    for id in idUser:
        try:
            id = int(id)
        except:
            badIds.append(id)
            continue

        if id > maxINT or id <= 0:
            badIds.append(id)
            continue

        user = User.query.filter_by(id = id).first()

        if not user or user.role == Role.Student:
            badIds.append(id)
            continue



    newMaturita = 
    db.session.add(newMaturita)
    db.session.commit()

    return send_response (201, 67121, {"message": "maturita created successfuly", "goodIds":goodIds, "badIds":badIds}, "success")"""
