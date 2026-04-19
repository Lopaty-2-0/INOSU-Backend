from flask import Blueprint
from src.models.Maturita import Maturita
from src.models.Evaluator import Evaluator
from src.models.User import User
import flask_login
from src.utils.response import send_response
from app import db, max_INT, limiter
from flask import request
from src.utils.paging import evaluator_paging
import datetime
from src.utils.redis_cache import set_cache, get_cache

evaluator_bp = Blueprint("evaluator", __name__)

@evaluator_bp.route("/evaluator/get", methods = ["GET"])
@flask_login.login_required
@limiter.limit("60/minute")
def get():
    amountForPaging = request.args.get("amountForPaging", None)
    pageNumber = request.args.get("pageNumber", None)
    searchQuery = request.args.get("searchQuery", None)
    idMaturita = request.args.get("idMaturita", None)
    cacheData = None

    allEvaluators = []

    if not amountForPaging:
        return send_response(400, 73010, {"message": "amountForPaging not entered"}, "error")

    try:
        amountForPaging = int(amountForPaging)
    except:
        return send_response(400, 73020, {"message": "amountForPaging not integer"}, "error")
    
    if amountForPaging < 1:
        return send_response(400, 73030, {"message": "amountForPaging smaller than 1"}, "error")
    
    if amountForPaging > max_INT:
        return send_response(400, 73040, {"message": "amountForPaging too big"}, "error")
    
    if not pageNumber:
        return send_response(400, 73050, {"message": "pageNumber not entered"}, "error")
    
    try:
        pageNumber = int(pageNumber)
    except:
        return send_response(400, 73060, {"message": "pageNumber not integer"}, "error")
    if pageNumber > max_INT + 1:
        return send_response(400, 73070, {"message": "pageNumber too big"}, "error")
    
    pageNumber -= 1

    if pageNumber < 0:
        return send_response(400, 73080, {"message": "pageNumber must be bigger than 0"}, "error")

    try:
        idMaturita = int(idMaturita)
    except:
        return send_response(400, 73090, {"message": "idMaturita not integer"}, "error")
    
    if idMaturita < 1 or idMaturita > max_INT:
        return send_response(400, 73100, {"message": "idMaturita not valid"}, "error")
    
    if not Maturita.query.filter_by(id = idMaturita).first():
        return send_response(404, 73110, {"message": "maturita not found"}, "error")
    
    cacheKey = f"evaluators:get:{idMaturita}:{amountForPaging}:{pageNumber}"

    if not searchQuery:
        cacheData = get_cache(cacheKey)

        if not cacheData:
            evaluators = Evaluator.query.filter_by(idMaturita = idMaturita).order_by(Evaluator.idUser.desc()).offset(amountForPaging * pageNumber).limit(amountForPaging)
            count = Evaluator.query.filter_by(idMaturita = idMaturita).count()
        else:
            allEvaluators = cacheData["evaluators"]
            count = cacheData["count"]
    else:
        evaluators, count = evaluator_paging(searchQuery = searchQuery, amountForPaging = amountForPaging, pageNumber = pageNumber, idMaturita = idMaturita)

    if not cacheData:
        for evaluator in evaluators:
            user = User.query.filter_by(id = evaluator.idUser).first()
            allEvaluators.append({"id":user.id, "name":user.name, "surname": user.surname, "abbreviation": user.abbreviation, "createdAt": user.createdAt, "role": user.role.value, "profilePicture":user.profilePicture, "email":user.email, "updatedAt":user.updatedAt})

        if not searchQuery:
            set_cache(cacheKey, {"evaluators": allEvaluators, "count":count})

    return send_response (201, 73121, {"message": "evaluators found successfuly", "evaluators": allEvaluators, "count":count}, "success")

@evaluator_bp.route("/evaluator/get/current", methods = ["GET"])
@flask_login.login_required
@limiter.limit("60/minute")
def get_current():
    amountForPaging = request.args.get("amountForPaging", None)
    pageNumber = request.args.get("pageNumber", None)
    searchQuery = request.args.get("searchQuery", None)
    cacheData = None

    now = datetime.datetime.now(tz=datetime.timezone.utc)

    allEvaluators = []

    if not amountForPaging:
        return send_response(400, 77010, {"message": "amountForPaging not entered"}, "error")

    try:
        amountForPaging = int(amountForPaging)
    except:
        return send_response(400, 77020, {"message": "amountForPaging not integer"}, "error")
    
    if amountForPaging < 1:
        return send_response(400, 77030, {"message": "amountForPaging smaller than 1"}, "error")
    
    if amountForPaging > max_INT:
        return send_response(400, 77040, {"message": "amountForPaging too big"}, "error")
    
    if not pageNumber:
        return send_response(400, 77050, {"message": "pageNumber not entered"}, "error")
    
    try:
        pageNumber = int(pageNumber)
    except:
        return send_response(400, 77060, {"message": "pageNumber not integer"}, "error")
    if pageNumber > max_INT + 1:
        return send_response(400, 77070, {"message": "pageNumber too big"}, "error")
    
    pageNumber -= 1

    if pageNumber < 0:
        return send_response(400, 77080, {"message": "pageNumber must be bigger than 0"}, "error")
    
    maturita = Maturita.query.filter((Maturita.endDate > now) & (Maturita.startDate < now)).first()

    if not maturita:
        return send_response(400, 77090, {"message": "no maturita in current time range"}, "error")
    
    cacheKey = f"evaluators:get:current:{amountForPaging}:{pageNumber}"

    if not searchQuery:
        cacheData = get_cache(cacheKey)

        if not cacheData:
            evaluators = Evaluator.query.filter_by(idMaturita = maturita.id).order_by(Evaluator.idUser.desc()).offset(amountForPaging * pageNumber).limit(amountForPaging)
            count = Evaluator.query.filter_by(idMaturita =  maturita.id).count()
        else:
            allEvaluators = cacheData["evaluators"]
            count = cacheData["count"]
    else:
        evaluators, count = evaluator_paging(searchQuery = searchQuery, amountForPaging = amountForPaging, pageNumber = pageNumber, idMaturita = maturita.id)

    if not cacheData:
        for evaluator in evaluators:
            user = User.query.filter_by(id = evaluator.idUser).first()
            allEvaluators.append({"id":user.id, "name":user.name, "surname": user.surname, "abbreviation": user.abbreviation, "createdAt": user.createdAt, "role": user.role.value, "profilePicture":user.profilePicture, "email":user.email, "updatedAt":user.updatedAt})

        if not searchQuery:
            set_cache(cacheKey, {"evaluators": allEvaluators, "count":count})

    return send_response (201, 77101, {"message": "evaluators found successfuly", "evaluators": allEvaluators, "count":count}, "success")