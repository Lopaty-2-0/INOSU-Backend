from app import db
from sqlalchemy.dialects.mysql import INTEGER

class Evaluator(db.Model):
    __tablename__ = "evaluator"
    idUser = db.Column(INTEGER(unsigned=True), db.ForeignKey("user.id", ondelete = "CASCADE"), primary_key = True)
    idMaturita = db.Column(INTEGER(unsigned=True), db.ForeignKey("maturita.id", ondelete = "CASCADE"), primary_key = True)    
    
    def __init__(self, idUser, idMaturita):
        self.idUser = idUser
        self.idMaturita = idMaturita

    def __repr__(self):
        return f"<evaluator{self.idUser, self.idMaturita!r}>"