from app import db
class User_Class(db.Model):
    __tablename__ = "user_class"
    idUser = db.Column(db.Integer, db.ForeignKey("user.id"), primary_key = True)
    idClass = db.Column(db.Integer, db.ForeignKey("class.id"), primary_key = True)    
    
    def __init__(self, idUser, idClass):
        self.idUser = idUser
        self.idClass = idClass

    def __repr__(self):
        return f"<task_class {self.idUser, self.idClass!r}>"