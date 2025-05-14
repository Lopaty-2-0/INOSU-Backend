import flask_login
from src.models.Specialization import Specialization
from src.models.Class import Class
from src.utils.response import sendResponse
from flask import request, Blueprint
from app import db

specialization_bp = Blueprint("specialization", __name__)

@specialization_bp.route("/specialization/add", methods = ["POST"])
@flask_login.login_required
def add():
    if flask_login.current_user.role != "admin":
        return sendResponse(400, 4010, {"message": "No permission for that"}, "error")
    
    data = request.get_json(force=True)
    name = data.get("name", None)
    abbrevation = data.get("abbrevation", None)
    lengthOfStudy = data.get("lengthOfStudy", None)

    if not lengthOfStudy:
        return sendResponse(400, 4020, {"message": "lengthOfStudy missing"}, "error")
    try:
        lengthOfStudy = int(lengthOfStudy)
    except:
        return sendResponse(400, 4030, {"message": "lengthOfStudy not integer"}, "error")
    if not abbrevation:
        return sendResponse(400, 4040, {"message": "abbrevation missing"}, "error")
    if len(abbrevation) > 1:
        return sendResponse(400, 4050, {"message": "abbrevation too long"}, "error")
    if Specialization.query.filter_by(abbrevation = abbrevation).first():
        return sendResponse(400, 4060, {"message": "abbrevation already in use"}, "error")
    if not name:
        return sendResponse(400, 4070, {"message": "name missing"}, "error")
    if len(name) > 100:
            return sendResponse(400, 4080, {"message": "Name too long"}, "error")
    if Specialization.query.filter_by(name = name).first():
        return sendResponse(400, 4090, {"message": "name already in use"}, "error")
    
    newSpecialization = Specialization(lengthOfStudy = lengthOfStudy, abbrevation = abbrevation, name = name)
    db.session.add(newSpecialization)
    db.session.commit()

    return sendResponse (201, 4101, {"message": "Specialization created successfuly", "specialization":{"lengthOfStudy":newSpecialization.lengthOfStudy, "abbrevation":newSpecialization.abbrevation, "name":newSpecialization.name}}, "success")

@specialization_bp.route("/specialization/delete", methods = ["DELETE"])
@flask_login.login_required
def delete():
    if flask_login.current_user.role != "admin":
        return sendResponse(400, 5010, {"message": "No permission for that"}, "error")
    
    data = request.get_json(force=True)
    idSpecialization = data.get("idSpecialization", None)

    if not idSpecialization:
        return sendResponse(400, 5020, {"message": "IdSpecialization is missing"}, "error")
    if not Specialization.query.filter_by(id = idSpecialization).first():
        return sendResponse(400, 5030, {"message": "Wrong idSpecialization"}, "error")
    if Class.query.filter_by(idSpecialization = idSpecialization).first():
        return sendResponse(400, 5040, {"message": "Some class still uses this specialization"}, "error")
    
    db.session.delete(Specialization.query.filter_by(id = idSpecialization).first())
    db.session.commit()
    
    return sendResponse (200, 5051, {"message": "Specialization deleted successfuly"}, "success")