from flask import Blueprint, request
from src.models.Task import Task
from src.models.User import User
from src.models.Event import Event
from src.models.User_Team import User_Team
import flask_login
from src.utils.response import send_response
from app import max_INT, db
from src.utils.event import create_event
from src.utils.all_user_classes import all_user_classes
from src.utils.enums import Event_Type, Role
import datetime
from sqlalchemy import func

event_bp = Blueprint("event_bp", __name__)

@event_bp.route("/event/add", methods = ["POST"])
@flask_login.login_required
def add():
    data = request.get_json(force=True)
    idUser = data.get("idUser", None)
    description = data.get("description", None)
    name = data.get("name", None)
    startDate = data.get("startDate", None)
    endDate = data.get("endDate", None)
    type = data.get("type", None)

    now = datetime.datetime.now(tz = datetime.timezone.utc)

    if not name:
        return send_response(400, 92010, {"message": "name missing"}, "error")
    if not endDate:
        return send_response(400, 92020, {"message": "endDate missing"}, "error")
    
    if idUser and flask_login.current_user.role != Role.Student:
        try:
            idUser = int(idUser)
        except:
            return send_response(400, 92030, {"message": "idUser not integer"}, "error")
        if idUser > max_INT or idUser <= 0:
            return send_response(400, 92040, {"message": "idUser not valid"}, "error")
        
        user = User.query.filter_by(id = idUser).first()

        if not user:
            return send_response(404, 92050, {"message": "Nonexistent user"}, "error")
        
        type = Event_Type.ByOther

    else:
        idUser = flask_login.current_user.id
    try:
        endDate = datetime.datetime.fromtimestamp(int(endDate)/1000, tz=datetime.timezone.utc)
    except:
        return send_response(400, 92060, {"message":"End date not integer or is too far"}, "error")
    if endDate < now:
        return send_response(400, 92070, {"message":"End date before now"}, "error")
    if startDate:
        try:
            startDate = datetime.datetime.fromtimestamp(int(startDate)/1000, tz=datetime.timezone.utc)
        except:
            return send_response(400, 92080, {"message":"startDate not integer or is too far"}, "error")
        if endDate.date() != startDate.date():
            return send_response(400, 92090, {"message":"endDate and startDate not on the same date"}, "error")
        if startDate < now:
            return send_response(400, 92100, {"message":"startDate before now"}, "error")
        if endDate <= startDate:
            return send_response(400, 92110, {"message":"endDate before startDate"}, "error")
    if type and not isinstance(type, Event_Type):
        if type not in [t.value for t in Event_Type]:
            return send_response(400, 92120, {"message": "Type not our type"}, "error")

        type = Event_Type(type)

        if type == Event_Type.ByOther and flask_login.current_user.role == Role.Student:
            return send_response(400, 92130, {"message": "Can not use this type"}, "error")
    
    name = str(name)

    if len(name) > 255:
        return send_response(400, 92140, {"message": "Name too long"}, "error")
    if description:
        description = str(description)
        if len(description) > 255:
            return send_response(400, 92150, {"message": "Description too long"}, "error")
    
    event = create_event(idUser, flask_login.current_user.id, name, description, startDate, endDate, type)

    return send_response(201, 92161, {"message": "event created successfuly", "event":{"idEvent": event.idEvent, "idUser":event.idUser, "maker":event.maker, "description":event.description, "startDate":event.startDate, "endDate":event.endDate, "name":event.name, "type":type.value if isinstance(type, Event_Type) else type}}, "success")

@event_bp.route("/event/delete", methods = ["DELETE"])
@flask_login.login_required
def delete():
    data = request.get_json(force=True)
    idEvent = data.get("idEvent", None)
    goodIds = []
    badIds = []

    if not idEvent:
        return send_response(400, 93010, {"message": "idEvent missing"}, "error")
    if not isinstance(idEvent, list):
        idEvent = [idEvent]

    for id in idEvent:
        try:
            id = int(id)
        except:
            badIds.append(id)
            continue
        if id > max_INT or id <= 0:
            badIds.append(id)
            continue

        event = Event.query.filter_by(idEvent = id, maker = flask_login.current_user.id).first()

        if not event:
            badIds.append(id)
            continue

        db.session.delete(event)
        goodIds.append(id)
    
    if not goodIds:
        return send_response(200, 93021, {"message": "nothing deleted"}, "success")
    
    db.session.commit()

    return send_response(200, 93031, {"message": "event deleted successfuly for current user", "goodIds":goodIds, "badIds":badIds}, "success")

@event_bp.route("/event/get", methods = ["GET"])
@flask_login.login_required
def get():
    amountForPaging = request.args.get("amountForPaging", None)
    pageNumber = request.args.get("pageNumber", None)
    date = request.args.get("date", None)
    count = 0

    allEvents = []
    tasks = []

    if not amountForPaging:
        return send_response(400, 94010, {"message": "amountForPaging not entered"}, "error")

    try:
        amountForPaging = int(amountForPaging)
    except:
        return send_response(400, 94020, {"message": "amountForPaging not integer"}, "error")
    
    if amountForPaging < 1:
        return send_response(400, 94030, {"message": "amountForPaging smaller than 1"}, "error")
    
    if amountForPaging > max_INT:
        return send_response(400, 94040, {"message": "amountForPaging too big"}, "error")
    
    if not pageNumber:
        return send_response(400, 94050, {"message": "pageNumber not entered"}, "error")
    
    try:
        pageNumber = int(pageNumber)
    except:
        return send_response(400, 94060, {"message": "pageNumber not integer"}, "error")
    if pageNumber > max_INT + 1:
        return send_response(400, 94070, {"message": "pageNumber too big"}, "error")
    
    pageNumber -= 1

    if pageNumber < 0:
        return send_response(400, 94080, {"message": "pageNumber must be bigger than 0"}, "error")
    try:
        date = datetime.datetime.fromtimestamp(int(date)/1000, tz=datetime.timezone.utc)
    except:
        return send_response(400, 94090, {"message":"date not integer or is too far"}, "error")
    
    
    events = Event.query.filter(Event.idUser == flask_login.current_user.id, func.date(Event.endDate) == date.date()).offset(pageNumber * amountForPaging).limit(amountForPaging)
    count += Event.query.filter(Event.idUser == flask_login.current_user.id, func.date(Event.endDate) == date.date()).count()

    pageNumber -= int(events.count()/amountForPaging)
    amountForPaging -= events.count()
    
    if amountForPaging:
        tasks = Task.query.join(User_Team, User_Team.idTask == Task.id & User_Team.guarantor == Task.guarantor).filter(func.date(Task.endDate) == date.date(), User_Team.idUser == flask_login.current_user.id).offset(pageNumber * amountForPaging).limit(amountForPaging)

    count += Task.query.join(User_Team, User_Team.idTask == Task.id & User_Team.guarantor == Task.guarantor).filter(func.date(Task.endDate) == date.date(), User_Team.idUser == flask_login.current_user.id).count()
    
    for event in events:
        user = User.query.filter_by(id = event.maker).first()

        userData = {"id": user.id, "name": user.name, "surname": user.surname, "abbreviation": user.abbreviation, "role": user.role.value, "profilePicture": user.profilePicture, "email": user.email, "idClass": all_user_classes(user.id), "createdAt":user.createdAt, "updatedAt":user.updatedAt, "reminders":user.reminders}

        if event.type:
            type = event.type.value
        else:
            type = None

        allEvents.append({"idEvent":event.idEvent, "user":userData, "name":event.name, "description":event.description, "startDate":event.startDate, "endDate":event.endDate, "type":type})

    for task in tasks:
        guarantorUser = User.query.filter_by(id = event.guarantor).first()

        guarantor = {"id": guarantorUser.id, "name": guarantorUser.name, "surname": guarantorUser.surname, "abbreviation": guarantorUser.abbreviation, "role": guarantorUser.role.value, "profilePicture": guarantorUser.profilePicture, "email": guarantorUser.email, "idClass": all_user_classes(guarantorUser.id), "createdAt":guarantorUser.createdAt, "updatedAt":guarantorUser.updatedAt, "reminders":guarantorUser.reminders}
        allEvents.append({"name": task.name, "endDate": task.endDate, "guarantor":guarantor, "type":task.type.value})

    return send_response(200, 94101, {"message": "events found successfuly", "events":allEvents, "count":count}, "success")

@event_bp.route("/event/get/id", methods = ["GET"])
@flask_login.login_required
def get_id():
    idEvent = request.args.get("idEvent", None)
    maker = request.args.get("maker", None)

    if not idEvent:
        return send_response(400, 95010, {"message": "idEvent missing"}, "error")
    try:
        idEvent = int(idEvent)
    except:
        return send_response(400, 95020, {"message": "idEvent not integer"}, "error")
    if idEvent > max_INT or idEvent <= 0:
        return send_response(400, 95030, {"message": "idEvent not valid"}, "error")
    if not maker:
        return send_response(400, 95040, {"message": "maker missing"}, "error")
    try:
        maker = int(maker)
    except:
        return send_response(400, 95050, {"message": "maker not integer"}, "error")
    if maker > max_INT or maker <= 0:
        return send_response(400, 95060, {"message": "maker not valid"}, "error")
    
    event = Event.query.filter_by(idEvent = idEvent, maker = maker, idUser = flask_login.current_user.id).first()
    
    if not event:
        return send_response(404, 95070, {"message": "Event not found"}, "error")
    
    if event.type:
        type = event.type.value
    else:
        type = None
    
    user = User.query.filter_by(id = maker).first()

    userData = {"id": user.id, "name": user.name, "surname": user.surname, "abbreviation": user.abbreviation, "role": user.role.value, "profilePicture": user.profilePicture, "email": user.email, "idClass": all_user_classes(user.id), "createdAt":user.createdAt, "updatedAt":user.updatedAt, "reminders":user.reminders}

    eventData = {"idEvent":event.idEvent, "maker":userData, "startDate":event.startDate, "endDate":event.endDate, "name":event.name, "description":event.description, "type":type}

    return send_response(200, 95081, {"message": "Event found successfuly", "event": eventData}, "success")

@event_bp.route("/event/get/maker/id", methods = ["GET"])
@flask_login.login_required
def get_id_maker():
    idEvent = request.args.get("idEvent", None)

    if not idEvent:
        return send_response(400, 96010, {"message": "idEvent missing"}, "error")
    try:
        idEvent = int(idEvent)
    except:
        return send_response(400, 96020, {"message": "idEvent not integer"}, "error")
    if idEvent > max_INT or idEvent <= 0:
        return send_response(400, 96030, {"message": "idEvent not valid"}, "error")
    
    event = Event.query.filter_by(idEvent = idEvent, maker = flask_login.current_user.id).first()
    
    if not event:
        return send_response(404, 96040, {"message": "Event not found"}, "error")
    
    if event.type:
        type = event.type.value
    else:
        type = None
    
    user = User.query.filter_by(id = event.idUser).first()

    userData = {"id": user.id, "name": user.name, "surname": user.surname, "abbreviation": user.abbreviation, "role": user.role.value, "profilePicture": user.profilePicture, "email": user.email, "idClass": all_user_classes(user.id), "createdAt":user.createdAt, "updatedAt":user.updatedAt, "reminders":user.reminders}

    eventData = {"idEvent":event.idEvent, "user":userData, "startDate":event.startDate, "endDate":event.endDate, "name":event.name, "description":event.description, "type":type}

    return send_response(200, 96051, {"message": "Event found successfuly", "event": eventData}, "success")

@event_bp.route("/event/get/maker", methods = ["GET"])
@flask_login.login_required
def get_maker():
    amountForPaging = request.args.get("amountForPaging", None)
    pageNumber = request.args.get("pageNumber", None)
    date = request.args.get("date", None)

    allEvents = []

    if not amountForPaging:
        return send_response(400, 97010, {"message": "amountForPaging not entered"}, "error")

    try:
        amountForPaging = int(amountForPaging)
    except:
        return send_response(400, 97020, {"message": "amountForPaging not integer"}, "error")
    
    if amountForPaging < 1:
        return send_response(400, 97030, {"message": "amountForPaging smaller than 1"}, "error")
    
    if amountForPaging > max_INT:
        return send_response(400, 97040, {"message": "amountForPaging too big"}, "error")
    
    if not pageNumber:
        return send_response(400, 97050, {"message": "pageNumber not entered"}, "error")
    
    try:
        pageNumber = int(pageNumber)
    except:
        return send_response(400, 97060, {"message": "pageNumber not integer"}, "error")
    if pageNumber > max_INT + 1:
        return send_response(400, 97070, {"message": "pageNumber too big"}, "error")
    
    pageNumber -= 1

    if pageNumber < 0:
        return send_response(400, 97080, {"message": "pageNumber must be bigger than 0"}, "error")
    
    try:
        date = datetime.datetime.fromtimestamp(int(date)/1000, tz=datetime.timezone.utc)
    except:
        return send_response(400, 97090, {"message":"date not integer or is too far"}, "error")
    
    
    events = Event.query.filter(Event.maker == flask_login.current_user.id, func.date(Event.endDate) == date.date()).offset(pageNumber * amountForPaging).limit(amountForPaging)
    count = Event.query.filter(Event.maker == flask_login.current_user.id, func.date(Event.endDate) == date.date()).count()

    for event in events:

        user = User.query.filter_by(id = event.idUser).first()

        userData = {"id": user.id, "name": user.name, "surname": user.surname, "abbreviation": user.abbreviation, "role": user.role.value, "profilePicture": user.profilePicture, "email": user.email, "idClass": all_user_classes(user.id), "createdAt":user.createdAt, "updatedAt":user.updatedAt, "reminders":user.reminders}

        if event.type:
            type = event.type.value
        else:
            type = None

        allEvents.append({"idEvent":event.idEvent, "user":userData, "name":event.name, "description":event.description, "startDate":event.startDate, "endDate":event.endDate, "type":type})

    return send_response(200, 97101, {"message": "events found successfuly", "events":allEvents, "count":count}, "success")


@event_bp.route("/event/get/week", methods = ["GET"])
@flask_login.login_required
def get_week():
    startDate = request.args.get("startDate", None)
    endDate = request.args.get("endDate", None)

    allEvents = []
    allTasks = []

    try:
        endDate = datetime.datetime.fromtimestamp(int(endDate)/1000, tz=datetime.timezone.utc)
    except:
        return send_response(400, 98010, {"message":"End date not integer or is too far"}, "error")
    try:
        startDate = datetime.datetime.fromtimestamp(int(startDate)/1000, tz=datetime.timezone.utc)
    except:
        return send_response(400, 98020, {"message":"startDate not integer or is too far"}, "error")
    
    if endDate <= startDate:
        return send_response(400, 98030, {"message":"endDate before startDate"}, "error")
    
    events = Event.query.filter(Event.idUser == flask_login.current_user.id, Event.endDate <= endDate, Event.endDate >= startDate)
    tasks = Task.query.join(User_Team, User_Team.idTask == Task.id & User_Team.guarantor == Task.guarantor).filter(Task.endDate >= startDate, Task.endDate <= endDate, User_Team.idUser == flask_login.current_user.id)

    for task in tasks:
        allTasks.append({"endDate": task.endDate, "type":task.type.value})

    for event in events:
        if event.type:
            type = event.type.value
        else:
            type = None

        allEvents.append({"endDate":event.endDate, "type":type})

    return send_response(200, 98041, {"message": "events found successfuly", "events":allEvents, "tasks":allTasks}, "success")

@event_bp.route("/event/get/maker/week", methods = ["GET"])
@flask_login.login_required
def get_maker_week():
    startDate = request.args.get("startDate", None)
    endDate = request.args.get("endDate", None)

    allEvents = []

    try:
        endDate = datetime.datetime.fromtimestamp(int(endDate)/1000, tz=datetime.timezone.utc)
    except: 
        return send_response(400, 99010, {"message":"End date not integer or is too far"}, "error")
    try:
        startDate = datetime.datetime.fromtimestamp(int(startDate)/1000, tz=datetime.timezone.utc)
    except:
        return send_response(400, 99020, {"message":"startDate not integer or is too far"}, "error")
    
    if endDate <= startDate:
        return send_response(400, 99030, {"message":"endDate before startDate"}, "error")
    
    events = Event.query.filter(Event.maker == flask_login.current_user.id, Event.endDate <= endDate, Event.endDate >= startDate)

    for event in events:
        if event.type:
            type = event.type.value
        else:
            type = None

        allEvents.append({"endDate":event.endDate, "type":type})

    return send_response(200, 99041, {"message": "events found successfuly", "events":allEvents}, "success")