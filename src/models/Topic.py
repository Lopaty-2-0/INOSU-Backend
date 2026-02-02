from app import db
from sqlalchemy.dialects.mysql import INTEGER

class Topic(db.Model):
    __tablename__ = "topic"

    id = db.Column(INTEGER(unsigned=True), primary_key = True, autoincrement = True)
    name = db.Column(db.VARCHAR(255), unique = True, nullable = False)


    def __init__(self, name):
        self.name = name


    def __repr__(self):
        return f"<topic {self.name!r}>"