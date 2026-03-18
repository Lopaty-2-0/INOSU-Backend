import flask_login
import os
from urllib.parse import quote
from app import pfp_path, task_path, hmac_ip
from flask import Blueprint, redirect
from src.utils.check_file import check_file_access
from src.utils.token import generate_hmac_token
from src.utils.response import send_response

check_file_bp = Blueprint("check_file_bp", __name__)

hmac_secret = os.getenv("HMAC_SECRET")
expiresIn = 600

@check_file_bp.route("/file/pfp/<string:filename>", methods = ["GET"])
@flask_login.login_required
@check_file_access("profilePictures")
def check_pfp(filename):
    filename = os.path.normpath(filename).replace("\\", "/")

    if filename.startswith(".."):
        return send_response(400, 44010, {"message": "Invalid path"}, "error")
    
    message = f"/downloads/{pfp_path}{filename}"
    token = generate_hmac_token(message)
    encoded_path = quote(message, safe="/")

    redirectUrl = f"{hmac_ip}{encoded_path}?token={token}"

    return redirect(redirectUrl)

@check_file_bp.route("/file/tasks/<string:guarantor>/<string:idTask>/<string:idTeam>/<string:idVersion>/<string:filename>", methods = ["GET"])
@flask_login.login_required 
@check_file_access("tasks")
def check_tasks(filename, idTask, idTeam, idVersion, guarantor):
    filename = os.path.normpath(filename).replace("\\", "/")
    
    if filename.startswith(".."):
        return send_response(400, 53010, {"message": "Invalid path"}, "error")
    
    message = f"/downloads/{task_path}{guarantor}/{idTask}/{idTeam}/{idVersion}/{filename}"
    token = generate_hmac_token(message)
    encoded_path = quote(message, safe="/")

    redirectUrl = f"{hmac_ip}{encoded_path}?token={token}"

    return redirect(redirectUrl)

@check_file_bp.route("/file/task/<string:guarantor>/<string:idTask>/<string:filename>", methods = ["GET"])
@flask_login.login_required
@check_file_access("task")
def check_task(filename, idTask, guarantor):
    filename = os.path.normpath(filename).replace("\\", "/")

    if filename.startswith(".."):
        return send_response(400, 58010, {"message": "Invalid path"}, "error")

    message = f"/downloads/{task_path}{guarantor}/{idTask}/{filename}"
    token = generate_hmac_token(message)
    encoded_path = quote(message, safe="/")

    redirectUrl = f"{hmac_ip}{encoded_path}?token={token}"

    return redirect(redirectUrl)