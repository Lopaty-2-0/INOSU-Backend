from flask import Blueprint
from src.models.Maturita import Maturita
from src.models.Maturita_Task import Maturita_Task
from src.models.Evaluator import Evaluator
from src.models.Task import Task
from src.models.Team import Team
from src.models.User_Team import User_Team
from src.models.User import User
from src.models.Topic import Topic
import flask_login

maturita_task_bp = Blueprint("maturita_task", __name__)

@flask_login.login_required
@maturita_task_bp.route("/maturita_task/get/table", methods = ["GET"])
def get_table():
    #TODO: udělat to prostě do excel tabulky
    #list s těmi pracemi(zaci) (sloupce:id žáka,příjmení žáka, jméno žáka, třída, zaměření, téma id, téma název, varianta id, varianta název, garant(zkratka), oponent (zkratka))
    #list s evaluator(ucitele) (sloupce:id učitele, jméno a příjmení učitele, zkratka, počet garancí, počet objector)
    #list s tématy(temata) (sloupce:id témata, název)
    return