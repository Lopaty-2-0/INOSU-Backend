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
expires_in = 600

@check_file_bp.route("/file/pfp/<string:filename>", methods = ["GET"])
@flask_login.login_required
@check_file_access("profilePictures")
def check_pfp(filename):
    message = pfp_path + filename
    expiry_timestamp = int(time.time()) + expires_in
    payload = f"{message}:{expiry_timestamp}"

    sig = hmac.new(
        hmac_secret.encode(),
        payload.encode(),
        hashlib.sha256
    ).digest()

    sig_hex = sig.hex()
    token_str = f"{payload}:{sig_hex}"
    token = base64.urlsafe_b64encode(token_str.encode()).decode().rstrip("=")

    redirect_url = f"{ip}{pfp_path}{quote(filename)}?token={quote(token)}"
    return redirect(redirect_url)


@check_file_bp.route("/file/tasks/<string:idTask>/<string:idTeam>/<string:idVersion>/<string:filename>", methods = ["GET"])
@flask_login.login_required
@check_file_access("tasks")
def check_tasks(filename, idTask, idTeam, idVersion):
    message = task_path + idTask + "/" + idTeam + "/" + idVersion + "/" + filename

    expiry_timestamp = int(time.time()) + expires_in
    payload = f"{message}:{expiry_timestamp}"

    sig = hmac.new(
        hmac_secret.encode(),
        payload.encode(),
        hashlib.sha256
    ).digest()

    sig_hex = sig.hex()
    token_str = f"{payload}:{sig_hex}"
    token = base64.urlsafe_b64encode(token_str.encode()).decode().rstrip("=")

    redirect_url = f"{ip}{task_path}{idTask}/{idTeam}/{idVersion}/{quote(filename)}?token={quote(token)}"
    return redirect(redirect_url)

@check_file_bp.route("/file/task/<string:idTask>/<string:filename>", methods = ["GET"])
@flask_login.login_required
@check_file_access("task")
def check_task(filename, idTask):
    message = task_path + idTask + "/" + filename

    expiry_timestamp = int(time.time()) + expires_in
    payload = f"{message}:{expiry_timestamp}"

    sig = hmac.new(
        hmac_secret.encode(),
        payload.encode(),
        hashlib.sha256
    ).digest()

    sig_hex = sig.hex()
    token_str = f"{payload}:{sig_hex}"
    token = base64.urlsafe_b64encode(token_str.encode()).decode().rstrip("=")

    redirect_url = f"{ip}{task_path}{idTask}/{quote(filename)}?token={quote(token)}"
    return redirect(redirect_url)