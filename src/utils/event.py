from src.models.Event import Event
from app import db

def create_event(idUser, maker, name, description, startDate, endDate, type):

    eventForId = Event.query.filter_by(maker = maker).order_by(Event.idEvent.desc()).first()

    id = eventForId.idEvent + 1 if eventForId else 1

    newEvent = Event(id, idUser, maker, name, description, startDate, endDate, type)
    db.session.add(newEvent)
    db.session.commit()

    return newEvent