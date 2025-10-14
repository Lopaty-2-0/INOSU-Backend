import flask_login
from functools import wraps
from app import task_path, pfp_path, ssh
from flask import request, session, abort
from src.utils.response import send_response
from src.utils.sftp_utils import sftp_stat_async
from src.models.Task import Task
from src.models.User import User
from src.models.User_Task import User_Task

def check_file_size(max_length):
    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            fileSize = request.content_length
            if fileSize != None and fileSize > max_length:
                return send_response(413, "F15010", {"message": "File exceeded max size"}, "error")
            return f(*args, **kwargs)
        return wrapper
    return decorator

"""
odsaď dolů je potřeba zkontrolovat
předpokládám že jsem retard a pochopil jsem to špatně
takže jestli se ti to nelíbí tak mi to napiš
"""

def check_file_access(folder_type):
    def decorator(func):
        @wraps(func)
        def wrapper(filename, id = None, id2=None, *args, **kwargs):
            idUser = flask_login.current_user.id
            if not idUser:
                abort(403)

            if folder_type == "profilePictures":
                if not has_access_to_pfp(idUser, filename):
                    abort(403)
            elif folder_type == "tasks":
                if not has_access_to_tasks(idUser, id, id2, filename):
                    abort(403)
            else:
                abort(403)

            return func(filename, id, id2, *args, **kwargs)
        return wrapper
    return decorator


"""
z nějakého důvodu stat dělá brikule (projde i kdyby neměl)
"""

def has_access_to_pfp(idUser, filename):
    if not idUser:
        return False
    
    if not User.query.filter_by(id = idUser).first():
        return False
    
    if flask_login.current_user.id != idUser and session.get("id") != idUser:
        return False
    
    if not sftp_stat_async(ssh, pfp_path + filename):
        return abort(404)
    print(pfp_path + filename)
    return True

def has_access_to_tasks(idUser, idTask, idStudent, filename):
    if not idUser:
        return False
    
    if not idTask:
        return False
    
    if not User.query.filter_by(id = idUser).first():
        return False
    
    if not Task.query.filter_by(id = idTask).first():
        return False
    
    if not User_Task.query.filter_by(idTask = idTask, idUser = idUser).first() and not Task.query.filter_by(id = idTask, guarantor = idUser).first():
        return False
    
    if not sftp_stat_async(ssh, task_path + idTask + "/" + idStudent + "/" + filename):
        return abort(404)

    return True