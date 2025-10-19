import flask_login
import flask_jwt_extended
import datetime
import time
import hmac
import hashlib
import os
import base64
from urllib.parse import quote
from app import pfp_path, task_path, url
from flask import Blueprint, redirect, request
from src.utils.check_file import check_file_access
from src.utils.response import send_response

check_file_bp = Blueprint("check_file_bp", __name__)

ip = os.getenv("HMAC_IP")
hmac_secret = os.getenv("HMAC_SECRET")
expires_in = 600 #rozhodni se jak dlouhý to chceš


@check_file_bp.route("/file/pfp/<string:filename>", methods = ["GET"])
@check_file_access("profilePictures")
@flask_login.login_required
def check_pfp(filename, id, id2, type):
    message = pfp_path + filename

    expiry_timestamp = int(time.time()) + expires_in

    payload = f"{message}:{expiry_timestamp}"
    token_signature = hmac.new(
        str(hmac_secret).encode(),
        payload.encode(),
        hashlib.sha256
    ).digest()

    token_data = f"{message}:{expiry_timestamp}".encode() + b":" + token_signature
    token = base64.urlsafe_b64encode(token_data).decode()

    redirect_url = f"{ip}{pfp_path}{quote(filename)}?token={quote(token)}"
    return redirect(redirect_url)


@check_file_bp.route("/file/tasks/<string:id>/<string:id2>/<string:type>/<string:filename>", methods = ["GET"])
@check_file_access("tasks")
@flask_login.login_required
def check_tasks(filename, id, id2, type):
    message = task_path + id + id2 + type + filename

    expiry_timestamp = int(time.time()) + expires_in

    payload = f"{message}:{expiry_timestamp}"
    token_signature = hmac.new(
        str(hmac_secret).encode(),
        payload.encode(),
        hashlib.sha256
    ).digest()

    token_data = f"{message}:{expiry_timestamp}".encode() + b":" + token_signature
    token = base64.urlsafe_b64encode(token_data).decode()

    redirect_url = f"{ip}{task_path}{id}{id2}{type}{quote(filename)}?token={quote(token)}"
    return redirect(redirect_url)

@check_file_bp.route("/file/task/<string:id>/<string:filename>", methods = ["GET"])
@check_file_access("task")
@flask_login.login_required
def check_task(filename, id, id2, type):
    message = task_path + id + filename

    expiry_timestamp = int(time.time()) + expires_in

    payload = f"{message}:{expiry_timestamp}"
    token_signature = hmac.new(
        str(hmac_secret).encode(),
        payload.encode(),
        hashlib.sha256
    ).digest()

    token_data = f"{message}:{expiry_timestamp}".encode() + b":" + token_signature
    token = base64.urlsafe_b64encode(token_data).decode()

    redirect_url = f"{ip}{task_path}{id}/{quote(filename)}?token={quote(token)}"
    return redirect(redirect_url)