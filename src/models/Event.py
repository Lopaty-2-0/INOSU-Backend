from app import db
from sqlalchemy.dialects.mysql import INTEGER
from src.utils.enums import Event_Type
import datetime

class Event(db.Model):
    __tablename__ = "event"
    idEvent = db.Column(INTEGER(unsigned=True), primary_key=True)
    idUser = db.Column(INTEGER(unsigned=True), db.ForeignKey("user.id", ondelete = "CASCADE"), nullable = False)
    maker = db.Column(INTEGER(unsigned=True), db.ForeignKey("user.id", ondelete = "CASCADE"), primary_key = True)
    name = db.Column(db.VARCHAR(255), nullable = False)
    description = db.Column(db.VARCHAR(500), nullable = True)
    startDate = db.Column(db.DateTime(timezone = True), default=lambda:datetime.datetime.now(datetime.timezone.utc), nullable=True)
    endDate = db.Column(db.DateTime(timezone = True), default=lambda:datetime.datetime.now(datetime.timezone.utc), nullable=False)
    type = db.Column(db.Enum(Event_Type), nullable = True)
    
    def __init__(self, idEvent, idUser, maker, name, description, startDate, endDate, type):
        self.idEvent = idEvent
        self.idUser = idUser
        self.maker = maker
        self.name = name
        self.description = description
        self.startDate = startDate
        self.endDate = endDate
        self.type = type

    def __repr__(self):
        return f"<evaluator{self.idUser, self.maker, self.name, self.description, self.startDate, self.endDate!r}>"