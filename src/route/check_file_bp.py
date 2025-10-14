import flask_login
import flask_jwt_extended
import datetime
from app import pfp_path, task_path
from flask import Blueprint, send_from_directory, redirect
from src.utils.check_file import check_file_access
from src.utils.response import send_response

check_file_bp = Blueprint("check_file_bp", __name__)

#nic nejede wheee

@check_file_bp.route("/file/pfp/<filename>", methods = ["GET"])
@check_file_access("profilePictures")
@flask_login.login_required
def check_pfp(filename, id, id2):
    token = flask_jwt_extended.create_access_token(fresh = True, identity= flask_login.current_user.email , expires_delta= datetime.timedelta(hours = 1),additional_claims = {"path": pfp_path, "filename": filename})
    link = "http://localhost:5000/file/get?token=" + token

    return send_response(200, 1, {"skibidi": "skibidi"}, "Error")


@check_file_bp.route("/file/task/<int:id>/<int:id2>/<filename>", methods = ["GET"])
@check_file_access("task")
@flask_login.login_required
def check_task(filename, id, id2):
    return send_response(200, 1, {"skibidi": "skibidi"}, "Error")


@check_file_bp.route("/file/get")
@flask_login.login_required
def give_file():
    return "SKIBIDI"