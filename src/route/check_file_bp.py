import flask_login
import time
import hmac
import hashlib
import os
import base64
from urllib.parse import quote
from app import pfp_path, task_path
from flask import Blueprint, redirect
from src.utils.check_file import check_file_access

check_file_bp = Blueprint("check_file_bp", __name__)

ip = os.getenv("HMAC_IP")
hmac_secret = os.getenv("HMAC_SECRET")
expiresIn = 600

@check_file_bp.route("/file/pfp/<string:filename>", methods = ["GET"])
@flask_login.login_required
@check_file_access("profilePictures")
def check_pfp(filename):
    message = pfp_path + filename
    expiryTimestamp = int(time.time()) + expiresIn
    payload = f"{message}:{expiryTimestamp}"

    sig = hmac.new(
        hmac_secret.encode(),
        payload.encode(),
        hashlib.sha256
    ).digest()

    sigHex = sig.hex()
    tokenStr = f"{payload}:{sigHex}"
    token = base64.urlsafe_b64encode(tokenStr.encode()).decode().rstrip("=")

    redirectUrl = f"{ip}{pfp_path}{quote(filename)}?token={quote(token)}"
    return redirect(redirectUrl)


@check_file_bp.route("/file/tasks/<string:guarantor>/<string:idTask>/<string:idTeam>/<string:idVersion>/<string:filename>", methods = ["GET"])
@flask_login.login_required
@check_file_access("tasks")
def check_tasks(filename, idTask, idTeam, idVersion, guarantor):
    message = task_path + guarantor + "/" + idTask + "/" + idTeam + "/" + idVersion + "/" + filename

    expiryTimestamp = int(time.time()) + expiresIn
    payload = f"{message}:{expiryTimestamp}"

    sig = hmac.new(
        hmac_secret.encode(),
        payload.encode(),
        hashlib.sha256
    ).digest()

    sigHex = sig.hex()
    tokenStr = f"{payload}:{sigHex}"
    token = base64.urlsafe_b64encode(tokenStr.encode()).decode().rstrip("=")

    redirectUrl = f"{ip}{task_path}{guarantor}/{idTask}/{idTeam}/{idVersion}/{quote(filename)}?token={quote(token)}"
    return redirect(redirectUrl)

@check_file_bp.route("/file/task/<string:guarantor>/<string:idTask>/<string:filename>", methods = ["GET"])
@flask_login.login_required
@check_file_access("task")
def check_task(filename, idTask, guarantor):
    message = task_path + guarantor + "/" + idTask + "/" + filename

    expiryTimestamp = int(time.time()) + expiresIn
    payload = f"{message}:{expiryTimestamp}"

    sig = hmac.new(
        hmac_secret.encode(),
        payload.encode(),
        hashlib.sha256
    ).digest()

    sigHex = sig.hex()
    tokenStr = f"{payload}:{sigHex}"
    token = base64.urlsafe_b64encode(tokenStr.encode()).decode().rstrip("=")

    redirectUrl = f"{ip}{task_path}{guarantor}/{idTask}/{quote(filename)}?token={quote(token)}"
    return redirect(redirectUrl)