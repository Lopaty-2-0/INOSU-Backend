import flask_login
from functools import wraps
from app import task_path, pfp_path, ssh
from flask import request, session, abort
from src.utils.response import send_response
from src.models.Task import Task
from src.models.User import User
from src.models.User_Team import User_Team
from src.models.Team import Team
from src.models.Version_Team import Version_Team

def check_file_size(maxLength):
        if not request.is_json:
            return send_response(400, "F15010", {"message": "JSON required"}, "error")

        data = request.get_json(silent=True) or {}
        declared_size = data.get("size")

        if declared_size is None:
            return send_response(400, "F15020", {"message": "Missing size"}, "error")

        if declared_size > maxLength:
            return send_response(413, "F15030", {"message": "File exceeded max size"}, "error")


def check_file_access(folder_type):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            idTask = kwargs.get("idTask")
            idTeam = kwargs.get("idTeam")
            idVersion = kwargs.get("idVersion")
            filename = kwargs.get("filename")
            guarantor = kwargs.get("guarantor")
            idUser = flask_login.current_user.id

            if not idUser:
                abort(403)

            if folder_type == "profilePictures":
                if not has_access_to_pfp(idUser, filename):
                    abort(403)
            elif folder_type == "tasks":
                if not has_access_to_tasks(idUser, idTask, idTeam, idVersion ,filename, guarantor):
                    abort(403)
            elif folder_type == "task":
                if not has_access_to_tasks(idUser, idTask, None, None, filename, guarantor):
                    abort(403)
            else:
                abort(403)

            return func(*args, **kwargs)
        return wrapper
    return decorator

def has_access_to_pfp(idUser, filename):
    if not idUser:
        return False
    
    if not filename:
        return False
    
    if not User.query.filter_by(id = idUser).first():
        return False
    
    if flask_login.current_user.id != idUser and session.get("id") != idUser:
        return False

    return True

def has_access_to_tasks(idUser, idTask, idTeam, idVersion, filename, guarantor):
    if not idUser:
        return False
    
    if not idTask:
        return False
    
    if not filename:
        return False
    
    if not guarantor:
        return False
    
    if not User.query.filter_by(id = idUser).first():
        return False
    
    if not User.query.filter_by(id = guarantor).first():
        return False
        
    task = Task.query.filter_by(id = idTask, guarantor = guarantor).first()
    
    if not task:
        return False

    userTeam = User_Team.query.filter_by(idTask = idTask, idUser = idUser, guarantor = guarantor).first()

    if not userTeam and task.guarantor != idUser:
        return False
    
    if not idTeam and not idVersion:
        path = task_path + guarantor + "/" + idTask + "/" + filename
    else:
        team = Team.query.filter_by(idTask = idTask, idTeam = idTeam, guarantor = guarantor).first()
        if not team:
            return False
        if userTeam:
            if userTeam.idTeam != team.idTeam:
                return False
        if not Version_Team.query.filter_by(idTask = idTask, idTeam = idTeam, idVersion = idVersion, guarantor = guarantor).first():
            return False
        
        path = task_path + guarantor + "/" + idTask + "/" + idTeam + "/" + idVersion + "/" + filename

    return True