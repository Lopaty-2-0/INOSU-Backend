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
from src.utils.enums import Role
from src.utils.response import send_response
from flask import request
from app import db, maxFLOAT, maxINT
import datetime

#TODO: otestovat
#TODO: přidat gety

maturita_bp = Blueprint("maturita", __name__)

@maturita_bp.route("/maturita/add", methods = ["POST"])
@flask_login.login_required
def add():
    if flask_login.current_user.role == Role.Student:
        return send_response(403, 67010, {"message": "No permission for that"}, "error")
    
    data = request.get_json(force=True)
    grade = data.get("grade", None)
    maxPoints = data.get("maxPoints", None)
    startDate = data.get("startDate", None)
    endDate = data.get("endDate", None)
    evaluators = data.get("evaluators", None)

    goodIds = []
    badIds = []

    if not grade:
        return send_response(400, 67020, {"message": "grade missing"}, "error")
    if not maxPoints:
         return send_response(400, 67030, {"message": "maxPoints missing"}, "error")
    if not startDate:
         return send_response(400, 67040, {"message": "startDate missing"}, "error")
    if not endDate:
         return send_response(400, 67050, {"message": "endDate missing"}, "error")
    
    grade = str(grade)

    if len(grade) > 9:
            return send_response(400, 67060, {"message": "grade too long"}, "error")
    if Maturita.query.filter_by(grade = grade).first():
        return send_response(400, 67070, {"message": "grade already in use"}, "error")
    
    try:
        maxPoints = float(maxPoints)
    except:
        return send_response(400, 67080, {"message":"maxPoints not float"}, "error")
    if maxPoints > maxFLOAT or maxPoints <= 0:
        return send_response(400, 67090, {"message": "maxPoints not valid"}, "error")  
    try:
        endDate = datetime.datetime.fromtimestamp(int(endDate)/1000, tz=datetime.timezone.utc)
    except:
        return send_response(400, 67100, {"message":"End date not integer or is too far"}, "error")
    try:
        startDate = datetime.datetime.fromtimestamp(int(startDate)/1000, tz=datetime.timezone.utc)
    except:
        return send_response(400, 67110, {"message":"startDate not integer or is too far"}, "error")
    if endDate <= startDate:
        return send_response(400, 67120, {"message":"Ending before begining"}, "error")
    
    newMaturita = Maturita(grade = grade, maxPoints = maxPoints, startDate = startDate, endDate = endDate)
    db.session.add(newMaturita)
    db.session.commit()

    if evaluators:
        if not isinstance(evaluators, list):
            evaluators = [evaluators]
        
        for evaluator in evaluators:
            try:
                evaluator = int(evaluator)
            except:
                badIds.append(evaluator)
                continue

            if evaluator > maxINT or evaluator <= 0:
                badIds.append(evaluator)
                continue

            user = User.query.filter_by(id = evaluator).first()

            if not user or user.role == Role.Student:
                badIds.append(evaluator)
                continue

            db.session.add(Evaluator(idUser = evaluator, idMaturita = newMaturita.id))
            goodIds.append(evaluator)

        db.session.commit()

    return send_response (201, 67131, {"message": "maturita created successfuly", "maturita":{"grade":newMaturita.grade, "id":newMaturita.id, "maxPoints":newMaturita.maxPoints, "startDate":newMaturita.startDate, "endDate":newMaturita.endDate}, "goodIds":goodIds, "badIds":badIds}, "success")


@maturita_bp.route("/maturita/update", methods = ["PuT"])
@flask_login.login_required
def update():
    if flask_login.current_user.role == Role.Student:
        return send_response(403, 68010, {"message": "No permission for that"}, "error")
    
    data = request.get_json(force=True)
    grade = data.get("grade", None)
    maxPoints = data.get("maxPoints", None)
    startDate = data.get("startDate", None)
    endDate = data.get("endDate", None)
    evaluators = data.get("evaluators", None)
    idMaturita = data.get("idMaturita", None)
    badIds = []
    goodIds = []


    if not idMaturita:
        return send_response(400, 68020, {"message": "idMaturita missing"}, "error")
    
    try:
        idMaturita = int(idMaturita)
    except:
        return send_response(400, 68030, {"message": "idMaturita not integer"}, "error")
    
    if idMaturita > maxINT or idMaturita <= 0:
        return send_response(400, 68040, {"message": "idMaturita not valid"}, "error")
    
    maturita = Maturita.query.filter_by(id = idMaturita).first()

    if not maturita:
        return send_response(400, 68050, {"message": "maturita not found"}, "error")
    
    if grade:
        grade = str(grade)

        if len(grade) > 9:
                return send_response(400, 68060, {"message": "grade too long"}, "error")
        if Maturita.query.filter_by(grade = grade).first() != maturita:
            return send_response(400, 68070, {"message": "grade already in use"}, "error")
        
        maturita.grade = grade
    
    if maxPoints:
        try:
            maxPoints = float(maxPoints)
        except:
            return send_response(400, 68080, {"message":"maxPoints not float"}, "error")
        if maxPoints > maxFLOAT or maxPoints <= 0:
            return send_response(400, 68090, {"message": "maxPoints not valid"}, "error")
        
        maturita.maxPoints = maxPoints
        
    if startDate:
        try:
            startDate = datetime.datetime.fromtimestamp(int(startDate)/1000, tz=datetime.timezone.utc)
        except:
            return send_response(400, 68100, {"message":"startDate not integer or is too far"}, "error")
        if maturita.endDate <= startDate:
            return send_response(400, 68110, {"message":"ending before beginning"}, "error")
        maturita.startDate = startDate
        
    if endDate:
        try:
            endDate = datetime.datetime.fromtimestamp(int(endDate)/1000, tz=datetime.timezone.utc)
        except:
            return send_response(400, 68120, {"message":"End date not integer or is too far"}, "error")
       
        if endDate <= maturita.startDate:
            return send_response(400, 68130, {"message":"Ending before beginning"}, "error")
        
        maturita.endDate = endDate
    
    db.session.commit()

    if evaluators:
        evaluatoring = Evaluator.query.filter_by(idMaturita = idMaturita)

        for evaluatored in evaluatoring:
            db.session.delete(evaluatored)
        db.session.commit()

        if not isinstance(evaluators, list):
            evaluators = [evaluators]
        
        for evaluator in evaluators:
            try:
                evaluator = int(evaluator)
            except:
                badIds.append(evaluator)
                continue

            if evaluator > maxINT or evaluator <= 0:
                badIds.append(evaluator)
                continue

            user = User.query.filter_by(id = evaluator).first()

            if not user or user.role == Role.Student:
                badIds.append(evaluator)
                continue

            db.session.add(Evaluator(idUser = evaluator, idMaturita = idMaturita))
            goodIds.append(evaluator)

        db.session.commit()

    return send_response (201, 68141, {"message": "maturita created successfuly", "maturita":{"grade":maturita.grade, "id":maturita.id, "maxPoints":maturita.maxPoints, "startDate":maturita.startDate, "endDate":maturita.endDate}, "goodIds":goodIds, "badIds": badIds}, "success")
