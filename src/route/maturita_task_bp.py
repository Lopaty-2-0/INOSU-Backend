from flask import Blueprint
from src.models.Maturita import Maturita
from src.models.Maturita_Task import Maturita_Task
from src.models.Evaluator import Evaluator
from src.models.Task import Task
from src.models.Team import Team
from src.models.User_Team import User_Team
from src.models.Version_Team import Version_Team

maturita_task_bp = Blueprint("maturita_task", __name__)