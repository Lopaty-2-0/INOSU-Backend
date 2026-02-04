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
from src.utils.paging import maturita_paging
from flask import request
from app import db, maxFLOAT, maxINT
import datetime
from src.utils.task import task_delete_sftp

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


@maturita_bp.route("/maturita/update", methods = ["PUT"])
@flask_login.login_required
async def update():
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
    if not grade and not isinstance(evaluators, list) and not startDate and not endDate and not maxPoints:
        return send_response(400, 68030, {"message": "nothing entered to change"}, "error")
    try:
        idMaturita = int(idMaturita)
    except:
        return send_response(400, 68040, {"message": "idMaturita not integer"}, "error")
    
    if idMaturita > maxINT or idMaturita <= 0:
        return send_response(400, 68050, {"message": "idMaturita not valid"}, "error")
    
    maturita = Maturita.query.filter_by(id = idMaturita).first()

    if not maturita:
        return send_response(400, 68060, {"message": "maturita not found"}, "error")
    
    if grade:
        grade = str(grade)
        id = maturita.id

        if len(grade) > 9:
                return send_response(400, 68070, {"message": "grade too long"}, "error")
        if Maturita.query.filter(Maturita.grade == grade).first():
            id = Maturita.query.filter(Maturita.grade == grade).first().id

        if id != maturita.id:
            return send_response(400, 68080, {"message": "grade already in use"}, "error")
        
        maturita.grade = grade
    
    if maxPoints:
        try:
            maxPoints = float(maxPoints)
        except:
            return send_response(400, 68090, {"message":"maxPoints not float"}, "error")
        if maxPoints > maxFLOAT or maxPoints <= 0:
            return send_response(400, 68100, {"message": "maxPoints not valid"}, "error")
        
        maturita.maxPoints = maxPoints
        
    if startDate:
        try:
            startDate = datetime.datetime.fromtimestamp(int(startDate)/1000, tz=datetime.timezone.utc)
        except:
            return send_response(400, 68110, {"message":"startDate not integer or is too far"}, "error")
        if maturita.endDate <= startDate:
            return send_response(400, 68120, {"message":"ending before beginning"}, "error")
        maturita.startDate = startDate
        
    if endDate:
        try:
            endDate = datetime.datetime.fromtimestamp(int(endDate)/1000, tz=datetime.timezone.utc)
        except:
            return send_response(400, 68130, {"message":"End date not integer or is too far"}, "error")
       
        if endDate <= maturita.startDate:
            return send_response(400, 68140, {"message":"Ending before beginning"}, "error")
        
        maturita.endDate = endDate
    
    db.session.commit()

    maturitas_tasks = Maturita_Task.query.filter_by(idMaturita = id).all()

    for maturitas in maturitas_tasks:
        task_maturita = Task.query.filter_by(id = maturitas.idTask, guarantor = maturitas.guarantor).first()
        task_maturita.endDate = maturita.endDate
        task_maturita.points = maturita.maxPoints

    if isinstance(evaluators, list):
        evaluatoring = Evaluator.query.filter_by(idMaturita = idMaturita).all()
        evaluator_ids = []

        for evaluatored in evaluatoring:
            evaluator_ids.append(evaluatored.idUser)
            db.session.delete(evaluatored)
        db.session.commit()
        
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

            if evaluator in evaluator_ids:
                evaluator_ids.remove(evaluator)

        for evaluator_id in evaluator_ids:
            maturita_tasks = Maturita_Task.query.filter_by(idMaturita = idMaturita, guarantor = evaluator_id).all()
            
            for maturita_task in maturita_tasks:

                task = Task.query.filter_by(id = maturita_task.idTask, guarantor = evaluator_id).first()
                team = Team.query.filter_by(idTask = maturita_task.idTask, guarantor = evaluator_id).first()
                user_team = User_Team.query.filter_by(idTeam = team.idTeam, idTask = team.idTask, guarantor = evaluator_id).first() 
                versions = Version_Team.query.filter_by(idTeam = team.idTeam, idTask = team.idTask, guarantor = evaluator_id).all()

                for version in versions:
                    db.session.delete(version)

                db.session.delete(user_team)
                db.session.delete(maturita_task)
                db.session.commit()
                db.session.delete(team)
                db.session.commit()
                await task_delete_sftp(task.id, task.guarantor)
                db.session.delete(task)

    db.session.commit()

    return send_response(201, 68151, {"message": "maturita updated successfuly", "maturita":{"grade":maturita.grade, "id":maturita.id, "maxPoints":maturita.maxPoints, "startDate":maturita.startDate, "endDate":maturita.endDate}, "goodIds":goodIds, "badIds": badIds}, "success")

@maturita_bp.route("/maturita/get/current", methods = ["GET"])
@flask_login.login_required
def get_current():
    now = datetime.datetime.now(tz=datetime.timezone.utc)
    maturita = Maturita.query.filter((Maturita.endDate > now) & (Maturita.startDate < now)).order_by(Maturita.id.desc()).first()

    if not maturita:
        return send_response(400, 69010, {"message": "no maturita in current time range"}, "error")
    
    evaluators = []
    actual_evaluators = Evaluator.query.filter_by(idMaturita = maturita.id)
    for evaluator in actual_evaluators:
        evaluators.append(evaluator.idUser)

    return send_response(201, 69021, {"message": "maturita found successfuly", "maturita":{"grade":maturita.grade, "id":maturita.id, "maxPoints":maturita.maxPoints, "startDate":maturita.startDate, "endDate":maturita.endDate, "evaluators":evaluators}}, "success")

@maturita_bp.route("/maturita/get/id", methods = ["GET"])
@flask_login.login_required
def get_id():
    id = request.args.get("id", None)

    if not id:
        return send_response(400, 70010, {"message": "id not entered"}, "error")
    
    try:
        id = int(id)
    except:
        return send_response(400, 70020, {"message": "id not integer"}, "error")
    
    if id > maxINT or id <=0:
        return send_response(400, 70030, {"message": "id not valid"}, "error")

    maturita = Maturita.query.filter_by(id = id).first()

    if not maturita:
        return send_response(400, 70040, {"message": "No maturita found"}, "error")
    
    evaluators = []
    actual_evaluators = Evaluator.query.filter_by(idMaturita = maturita.id)
    for evaluator in actual_evaluators:
        evaluators.append(evaluator.idUser)
    
    return send_response(201, 70051, {"message": "maturita found successfuly", "maturita":{"grade":maturita.grade, "id":maturita.id, "maxPoints":maturita.maxPoints, "startDate":maturita.startDate, "endDate":maturita.endDate, "evaluators":evaluators}}, "success")

@maturita_bp.route("/maturita/delete", methods = ["delete"])
@flask_login.login_required
async def delete():
    data = request.get_json(force=True)
    idMaturita = data.get("id", None)
    badIds = []
    goodIds = []

    if flask_login.current_user.role == Role.Student:
        return send_response(403, 71010, {"message": "No permission for that"}, "error")

    if not idMaturita:
        return send_response(400, 71020, {"message": "id not entered"}, "error")
    
    if not isinstance(idMaturita, list):
        idMaturita = [idMaturita]
    
    for id in idMaturita:
        try:
            id = int(id)
        except:
            badIds.append(id)
            continue
        
        if id > maxINT or id <=0:
            badIds.append(id)
            continue

        maturita = Maturita.query.filter_by(id = id).first()

        if not maturita:
            badIds.append(id)
            continue
    
        maturita_tasks = Maturita_Task.query.filter_by(idMaturita = id)
        evaluators = Evaluator.query.filter_by(idMaturita = id).all()

        for evaluator in evaluators:
            db.session.delete(evaluator)
        db.session.commit()

        for maturita_task in maturita_tasks:
            task = Task.query.filter_by(id = maturita_task.idTask, guarantor = maturita_task.guarantor).first()
            team = Team.query.filter_by(idTask = maturita_task.idTask, guarantor = maturita_task.guarantor).first()
            user_team = User_Team.query.filter_by(idTeam = team.idTeam, idTask = team.idTask, guarantor = team.guarantor).first() 
            versions = Version_Team.query.filter_by(idTeam = team.idTeam, idTask = team.idTask, guarantor = team.guarantor).all()

            for version in versions:
                db.session.delete(version)

            if user_team:
                db.session.delete(user_team)
            if maturita_task:
                db.session.delete(maturita_task)
            db.session.commit()
            if team:
                db.session.delete(team)
                db.session.commit()
            if task:
                await task_delete_sftp(task.id, task.guarantor)
                db.session.delete(task)
            
        db.session.delete(maturita)
        goodIds.append(id)
        db.session.commit()

    if not goodIds:
        return send_response(400, 71030, {"message": "no deletion"}, "error")

    return send_response(201, 71041, {"message": "maturita deleted successfuly", "goodIds":goodIds, "badIds":badIds}, "success")

@maturita_bp.route("/maturita/get", methods = ["GET"])
@flask_login.login_required
def get():
    amountForPaging = request.args.get("amountForPaging", None)
    pageNumber = request.args.get("pageNumber", None)
    searchQuery = request.args.get("searchQuery", None)

    all_maturitas = []

    if not amountForPaging:
        return send_response(400, 72010, {"message": "amountForPaging not entered"}, "error")

    try:
        amountForPaging = int(amountForPaging)
    except:
        return send_response(400, 72020, {"message": "amountForPaging not integer"}, "error")
    
    if amountForPaging < 1:
        return send_response(400, 72030, {"message": "amountForPaging smaller than 1"}, "error")
    
    if amountForPaging > maxINT:
        return send_response(400, 72040, {"message": "amountForPaging too big"}, "error")
    
    if not pageNumber:
        return send_response(400, 72050, {"message": "pageNumber not entered"}, "error")
    
    try:
        pageNumber = int(pageNumber)
    except:
        return send_response(400, 72060, {"message": "pageNumber not integer"}, "error")
    if pageNumber > maxINT + 1:
        return send_response(400, 72070, {"message": "pageNumber too big"}, "error")
    
    pageNumber -= 1

    if pageNumber < 0:
        return send_response(400, 72080, {"message": "pageNumber must be bigger than 0"}, "error")

    if not searchQuery:
        maturitas = Maturita.query.order_by(Maturita.id.desc()).offset(amountForPaging * pageNumber).limit(amountForPaging)
        count = Maturita.query.count()
    else:
        maturitas, count = maturita_paging(searchQuery = searchQuery, amountForPaging = amountForPaging, pageNumber = pageNumber)

    for maturita in maturitas:
        evaluators = []
        actual_evaluators = Evaluator.query.filter_by(idMaturita = maturita.id)
        for evaluator in actual_evaluators:
            evaluators.append(evaluator.idUser)
        all_maturitas.append({"grade":maturita.grade, "id":maturita.id, "maxPoints":maturita.maxPoints, "startDate":maturita.startDate, "endDate":maturita.endDate, "evaluators":evaluators})

    return send_response(201, 72091, {"message": "maturita created successfuly", "maturita":all_maturitas, "count":count}, "success")
