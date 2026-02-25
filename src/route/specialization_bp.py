import flask_login
from src.models.Specialization import Specialization
from src.utils.paging import specialization_paging
from src.utils.response import send_response
from src.utils.enums import Role
from flask import request, Blueprint, send_file
from app import db, max_INT
from src.utils.check_file import check_file_size
import json
import io

#TODO: přidat export + import (json)

specialization_bp = Blueprint("specialization", __name__)

@specialization_bp.route("/specialization/add", methods = ["POST"])
@flask_login.login_required
def add():
    if flask_login.current_user.role != Role.Admin:
        return send_response(403, 4010, {"message": "No permission for that"}, "error")
    
    data = request.get_json(force=True)
    name = data.get("name", None)
    abbreviation = data.get("abbreviation", None)
    lengthOfStudy = data.get("lengthOfStudy", None)

    if not lengthOfStudy:
        return send_response(400, 4020, {"message": "lengthOfStudy missing"}, "error")
    if not abbreviation:
        return send_response(400, 4030, {"message": "abbreviation missing"}, "error")
    if not name:
        return send_response(400, 4040, {"message": "name missing"}, "error")
    
    name = str(name)
    
    try:
        lengthOfStudy = int(lengthOfStudy)
    except:
        return send_response(400, 4050, {"message": "lengthOfStudy not integer"}, "error")
    if lengthOfStudy > max_INT or lengthOfStudy <= 0:
        return send_response(400, 4060, {"message": "lengthOfStudy not valid"}, "error")
    if len(abbreviation) > 1:
        return send_response(400, 4070, {"message": "abbreviation too long"}, "error")
    if Specialization.query.filter_by(abbreviation = abbreviation).first():
        return send_response(400, 4080, {"message": "abbreviation already in use"}, "error")
    if len(name) > 45:
            return send_response(400, 4090, {"message": "Name too long"}, "error")
    if Specialization.query.filter_by(name = name).first():
        return send_response(400, 4100, {"message": "name already in use"}, "error")
    
    newSpecialization = Specialization(lengthOfStudy = lengthOfStudy, abbreviation = abbreviation, name = name)
    db.session.add(newSpecialization)
    db.session.commit()

    return send_response (201, 4111, {"message": "Specialization created successfuly", "specialization":{"lengthOfStudy":newSpecialization.lengthOfStudy, "abbreviation":newSpecialization.abbreviation, "name":newSpecialization.name, "id":newSpecialization.id}}, "success")

@specialization_bp.route("/specialization/add/file", methods = ["POST"])
@flask_login.login_required
def add_file():
    if flask_login.current_user.role != Role.Admin:
        return send_response(403, 101010, {"message": "No permission for that"}, "error")
    
    allSpecializations = 0
    goodSpecializations = 0
    badSpecializations = []

    specializations = request.files.get("jsonFile", None)

    if not specializations:
        return send_response(400, 101020, {"message": "File is missing"}, "error")
    
    if len(specializations.filename.rsplit(".", 1)) < 2 or specializations.filename.rsplit(".", 1)[1].lower() != "json":
        return send_response(400, 101030, {"message": "Wrong file format"}, "error")
    
    response = check_file_size(4*1024*1024, specializations.tell())

    if response:
        return response
    
    file_content = specializations.read().decode("utf-8").strip()

    if not file_content:
        return send_response(400, 101040, {"message": "File is empty"}, "error")

    try:
        data = json.loads(file_content)
    except json.JSONDecodeError:
        return send_response(400, 101050, {"message": "Invalid JSON format"}, "error")
    
    for specializationData in data.get("specializations", []):
        name = specializationData.get("name", None)
        lengthOfStudy = specializationData.get("lengthOfStudy", None)
        abbreviation = specializationData.get("abbreviation", None)

        allSpecializations += 1

        if not lengthOfStudy and not abbreviation and not name:
            specializationResponse, status = send_response(400, 101060, {"message": "Nothing entered", "specializationNumber":allSpecializations}, "error")
            badSpecializations.append(specializationResponse)
            continue
        
        abbreviation = str(abbreviation)
        name = str(name)
        
        try:
            lengthOfStudy = int(lengthOfStudy)
        except:
            specializationResponse, status = send_response(400, 101070, {"message": "lengthOfStudy not integer", "specializationNumber":allSpecializations}, "error")
            badSpecializations.append(specializationResponse)
            continue

        if lengthOfStudy > max_INT or lengthOfStudy <= 0:
            specializationResponse, status = send_response(400, 101080, {"message": "lengthOfStudy not valid", "specializationNumber":allSpecializations}, "error")
            badSpecializations.append(specializationResponse)
            continue

        if len(abbreviation) > 1 or Specialization.query.filter_by(abbreviation = abbreviation).first():
            specializationResponse, status =send_response(400, 101090, {"message": "Abbreviation too long or already in use", "specializationNumber":allSpecializations}, "error")
            badSpecializations.append(specializationResponse)
            continue

        if len(name)>45 or Specialization.query.filter_by(name = name).first():
            specializationResponse, status =send_response(400, 101110, {"message": "name too long or already in use", "specializationNumber":allSpecializations}, "error")
            badSpecializations.append(specializationResponse)
            continue

        newSpecialization = Specialization(lengthOfStudy = lengthOfStudy, abbreviation = abbreviation, name=name)
        db.session.add(newSpecialization)

        goodSpecializations += 1

    db.session.commit()
    
    if goodSpecializations == 0:
        return send_response (400, 101120, {"message": "No specializations created", "badSpecializations":badSpecializations}, "error") 
            
    return send_response (201, 101131, {"message": "Specializations created successfuly", "badSpecializations":badSpecializations}, "success")

@specialization_bp.route("/specialization/get/file", methods = ["GET"])
@flask_login.login_required
def get_file():
    if flask_login.current_user.role != Role.Admin:
        return send_response(403, 104010, {"message": "No permission for that"}, "error")

    specializations = Specialization.query.all()

    data = {"specializations":[]}
    
    for specialization in specializations:
        data["specializations"].append({"name":specialization.name, "lengthOfStudy":specialization.lengthOfStudy, "abbreviation":specialization.abbreviation})

    buffer = io.BytesIO()
    buffer.write(json.dumps(data, indent=4, ensure_ascii=False).encode("utf-8"))
    buffer.seek(0)

    # send_response(200, 104021, {"message": "Specializations found successfuly"}, "success")

    return send_file(buffer, as_attachment = True, download_name = "specializations.json", mimetype = "application/json")

@specialization_bp.route("/specialization/delete", methods = ["DELETE"])
@flask_login.login_required
def delete():
    badIds = []
    goodIds = []
    
    if flask_login.current_user.role != Role.Admin:
        return send_response(403, 5010, {"message": "No permission for that"}, "error")
    
    data = request.get_json(force=True)
    idSpecialization = data.get("id", None)

    if not idSpecialization:
        return send_response(400, 5020, {"message": "Id is missing"}, "error")
    if not isinstance(idSpecialization, list):
        idSpecialization = [idSpecialization]
    
    for id in idSpecialization:
        try:
            id = int(id)
        except:
            badIds.append(id)
            continue

        if id > max_INT or id <= 0:
            badIds.append(id)
            continue

        if not Specialization.query.filter_by(id = id).first() :
            badIds.append(id)
            continue

        db.session.delete(Specialization.query.filter_by(id = id).first())
        goodIds.append(id)

    db.session.commit()
    
    if not goodIds:
        return send_response (400, 5030, {"message": "No deletion"}, "error")
    
    return send_response (200, 5041, {"message": "Specializations deleted successfuly", "goodIds":goodIds, "badIds":badIds}, "success")

@specialization_bp.route("/specialization/get", methods = ["GET"])
@flask_login.login_required
def get():
    amountForPaging = request.args.get("amountForPaging", None)
    pageNumber = request.args.get("pageNumber", None)
    searchQuery = request.args.get("searchQuery", None)

    specializations = []

    if not amountForPaging:
        return send_response(400, 29010, {"message": "amountForPaging not entered"}, "error")

    try:
        amountForPaging = int(amountForPaging)
    except:
        return send_response(400, 29020, {"message": "amountForPaging not integer"}, "error")
    
    if amountForPaging < 1:
        return send_response(400, 29030, {"message": "amountForPaging smaller than 1"}, "error")
    
    if amountForPaging > max_INT:
        return send_response(400, 29040, {"message": "amountForPaging too big"}, "error")
    
    if not pageNumber:
        return send_response(400, 29050, {"message": "pageNumber not entered"}, "error")
    
    try:
        pageNumber = int(pageNumber)
    except:
        return send_response(400, 29060, {"message": "pageNumber not integer"}, "error")
    if pageNumber > max_INT + 1:
        return send_response(400, 29070, {"message": "amountForPaging too big"}, "error")
    
    pageNumber -= 1

    if pageNumber < 0:
        return send_response(400, 29080, {"message": "pageNumber must be bigger than 0"}, "error")

    if not searchQuery:
        specialization = Specialization.query.order_by(Specialization.id.desc()).offset(amountForPaging * pageNumber).limit(amountForPaging)
        count = Specialization.query.count()
    else:
        specialization, count = specialization_paging(amountForPaging = amountForPaging, pageNumber = pageNumber, searchQuery = searchQuery)

    for s in specialization:
        specializations.append({"id":s.id,"name":s.name, "abbreviation":s.abbreviation, "lengthOfStudy":s.lengthOfStudy})

    return send_response (200, 29091, {"message": "Specializations found", "specializations":specializations, "count":count}, "success")

@specialization_bp.route("/specialization/get/id", methods=["GET"])
@flask_login.login_required
def get_by_id():
    id = request.args.get("id", None)

    if not id:
        return send_response(400, 54010, {"message": "Id not entered"}, "error")
    try:
        id = int(id)
    except:
        return send_response(400, 54020, {"message": "Id not integer"}, "error")
    if id > max_INT or id <=0:
        return send_response(400, 54030, {"message": "Id not valid"}, "error")

    specialization = Specialization.query.filter_by(id=id).first()
    
    if not specialization:
        return send_response(404, 54040, {"message": "Specialization not found"}, "error")

    return send_response(200, 54051, {"message": "Specialization found", "specialization": {"id":specialization.id,"name":specialization.name, "abbreviation":specialization.abbreviation, "lengthOfStudy":specialization.lengthOfStudy}}, "success")
