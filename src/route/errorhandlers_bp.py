from flask import Blueprint
from src.utils.response import send_response

errors_bp = Blueprint("errors", __name__)

@errors_bp.app_errorhandler(400)
def bad_request(e):
    return send_response(400, "E10010", {"message": "Bad Request"}, "error")

@errors_bp.app_errorhandler(401)
def unauthorized(e):
    return send_response(401, "E10020", {"message": "Unauthorized"}, "error")

@errors_bp.app_errorhandler(404)
def page_not_found(e):
    return send_response(404, "E10030", {"message": "Page Not Found"}, "error")

@errors_bp.app_errorhandler(405)
def method_not_allowed(e):
    return  send_response(405, "E10040", {"message": "Method Not Allowed"}, "error")

@errors_bp.app_errorhandler(413)
def method_not_allowed(e):
    return  send_response(413, "E10050", {"message": "Payload Too Large"}, "error")

@errors_bp.app_errorhandler(500)
def server_error(e):
    return  send_response(500, "E10060", {"message": "Internal Server Error"}, "error")

@errors_bp.app_errorhandler(504)
def timeout(e):
    return  send_response(504, "E10070", {"message": "Gateway Time-out"}, "error")

@errors_bp.app_errorhandler(403)
def method_not_allowed(e):
    return  send_response(403, "E10080", {"message": "Forbidden"}, "error")