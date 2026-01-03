from app import db
from sqlalchemy.dialects.mysql import INTEGER

class User_Class(db.Model):
    __tablename__ = "user_class"
    idUser = db.Column(INTEGER(unsigned=True), db.ForeignKey("user.id"), primary_key = True)
    idClass = db.Column(INTEGER(unsigned=True), db.ForeignKey("class.id"), primary_key = True)    
    
    def __init__(self, idUser, idClass):
        self.idUser = idUser
        self.idClass = idClass

    def __repr__(self):
        return f"<user_class {self.idUser, self.idClass!r}>"