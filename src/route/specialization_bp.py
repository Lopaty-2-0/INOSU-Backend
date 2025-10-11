import flask_login
from src.models.Specialization import Specialization
from src.models.Class import Class
from src.utils.response import send_response
from flask import request, Blueprint
from app import db

specialization_bp = Blueprint("specialization", __name__)

@specialization_bp.route("/specialization/add", methods = ["POST"])
@flask_login.login_required
def add():
    if flask_login.current_user.role != "admin":
        return send_response(403, 4010, {"message": "No permission for that"}, "error")
    
    data = request.get_json(force=True)
    name = data.get("name", None)
    abbreviation = data.get("abbreviation", None)
    lengthOfStudy = data.get("lengthOfStudy", None)

    if not lengthOfStudy:
        return send_response(400, 4020, {"message": "lengthOfStudy missing"}, "error")
    try:
        lengthOfStudy = int(lengthOfStudy)
        if lengthOfStudy > 2147483647:
            lengthOfStudy = "a"
            lengthOfStudy = int(lengthOfStudy)
    except:
        return send_response(400, 4030, {"message": "lengthOfStudy not integer"}, "error")
    if not abbreviation:
        return send_response(400, 4040, {"message": "abbreviation missing"}, "error")
    if len(abbreviation) > 1:
        return send_response(400, 4050, {"message": "abbreviation too long"}, "error")
    if Specialization.query.filter_by(abbreviation = abbreviation).first():
        return send_response(400, 4060, {"message": "abbreviation already in use"}, "error")
    if not name:
        return send_response(400, 4070, {"message": "name missing"}, "error")
    if len(name) > 100:
            return send_response(400, 4080, {"message": "Name too long"}, "error")
    if Specialization.query.filter_by(name = name).first():
        return send_response(400, 4090, {"message": "name already in use"}, "error")
    
    newSpecialization = Specialization(lengthOfStudy = lengthOfStudy, abbreviation = abbreviation, name = name)
    db.session.add(newSpecialization)
    db.session.commit()

    return send_response (201, 4101, {"message": "Specialization created successfuly", "specialization":{"lengthOfStudy":newSpecialization.lengthOfStudy, "abbreviation":newSpecialization.abbreviation, "name":newSpecialization.name, "id":newSpecialization.id}}, "success")

@specialization_bp.route("/specialization/delete", methods = ["DELETE"])
@flask_login.login_required
def delete():
    badIds = []
    classIds = []
    goodIds = []
    
    if flask_login.current_user.role != "admin":
        return send_response(403, 5010, {"message": "No permission for that"}, "error")
    
    data = request.get_json(force=True)
    idSpecialization = data.get("idSpecialization", None)

    if not idSpecialization:
        return send_response(400, 5020, {"message": "IdSpecialization is missing"}, "error")
    if not isinstance(idSpecialization, list):
        idSpecialization = [idSpecialization]
    
    for id in idSpecialization:
        if not Specialization.query.filter_by(id = id).first():
            badIds.append(id)
            continue
        if Class.query.filter_by(idSpecialization = id).first():
            classIds.append(id)
            continue

        db.session.delete(Specialization.query.filter_by(id = id).first())
        goodIds.append(id)

    db.session.commit()
    
    if not goodIds:
        return send_response (400, 5030, {"message": "No deletion"}, "error")
    
    return send_response (200, 5041, {"message": "Specializations deleted successfuly", "goodIds":goodIds, "badIds":badIds, "classIds":classIds}, "success")

@specialization_bp.route("/specialization/get", methods = ["GET"])
@flask_login.login_required
def get():
    specialization = Specialization.query.all()
    specializations = []

    if not specialization:
        return send_response (400, 29010, {"message": "No specialization found"}, "error")
    
    for s in specialization:
        specializations.append({"id":s.id,"name":s.name, "abbreviation":s.abbreviation, "lengthOfStudy":s.lengthOfStudy})

    return send_response (200, 29021, {"message": "Specializations found", "specializations":specializations}, "success")