from flask import Blueprint
from src.utils.response import sendResponse

errors_bp = Blueprint("errors", __name__)

@errors_bp.app_errorhandler(400)
def bad_request(e):
    return sendResponse(400, "E10010", {"message": "Bad request"}, "error")

@errors_bp.app_errorhandler(401)
def unauthorized(e):
    return sendResponse(401, "E10010", {"message": "Unauthorized"}, "error")

@errors_bp.app_errorhandler(404)
def page_not_found(e):
    return sendResponse(404, "E10030", {"message": "Page not found"}, "error")

@errors_bp.app_errorhandler(405)
def method_not_allowed(e):
    return  sendResponse(405, "E10040", {"message": "Method Not Allowed"}, "error")

@errors_bp.app_errorhandler(413)
def method_not_allowed(e):
    return  sendResponse(413, "E10050", {"message": "Payload Too Large"}, "error")

@errors_bp.app_errorhandler(500)
def server_error(e):
    return  sendResponse(500, "E10060", {"message": "Internal server error"}, "error")

@errors_bp.app_errorhandler(504)
def timeout(e):
    return  sendResponse(504, "E10070", {"message": "Gateway Time-out"}, "error")
