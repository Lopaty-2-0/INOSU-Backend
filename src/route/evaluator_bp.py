from flask import Blueprint
from src.models.Maturita import Maturita
from src.models.Evaluator import Evaluator
from src.models.User import User
import flask_login
from src.utils.response import send_response
from app import db, maxINT
from flask import request

evaluator_bp = Blueprint("evaluator", __name__)

"""@evaluator_bp.route("/evaluator/get", methods = ["GET"])
@flask_login.login_required
def get():
    amountForPaging = request.args.get("amountForPaging", None)
    pageNumber = request.args.get("pageNumber", None)
    searchQuery = request.args.get("searchQuery", None)

    all_evaluators = []

    if not amountForPaging:
        return send_response(400, 73010, {"message": "amountForPaging not entered"}, "error")

    try:
        amountForPaging = int(amountForPaging)
    except:
        return send_response(400, 73020, {"message": "amountForPaging not integer"}, "error")
    
    if amountForPaging < 1:
        return send_response(400, 73030, {"message": "amountForPaging smaller than 1"}, "error")
    
    if amountForPaging > maxINT:
        return send_response(400, 73040, {"message": "amountForPaging too big"}, "error")
    
    if not pageNumber:
        return send_response(400, 73050, {"message": "pageNumber not entered"}, "error")
    
    try:
        pageNumber = int(pageNumber)
    except:
        return send_response(400, 73060, {"message": "pageNumber not integer"}, "error")
    if pageNumber > maxINT + 1:
        return send_response(400, 73070, {"message": "pageNumber too big"}, "error")
    
    pageNumber -= 1

    if pageNumber < 0:
        return send_response(400, 73080, {"message": "pageNumber must be bigger than 0"}, "error")

    if not searchQuery:
        evaluators = Evaluator.query.order_by(Evaluator.idMaturita.desc()).offset(amountForPaging * pageNumber).limit(amountForPaging)
        count = Evaluator.query.count()
    else:
        evaluators, count = evaluator_paging(searchQuery = searchQuery, amountForPaging = amountForPaging, pageNumber = pageNumber)
    

    return send_response (201, 73121, {"message": "evaluators found successfuly", "evaluators": all_evaluators}, "success")"""
