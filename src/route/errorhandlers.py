from flask import Blueprint
from src.utils.response import sendResponse

errors_bp = Blueprint("errors", __name__)

@errors_bp.app_errorhandler(401)
def unauthorized(e):
    return sendResponse(401, 1, {"message": "Unauthorized"}, "error")

@errors_bp.app_errorhandler(400)
def bad_request(e):
    return sendResponse(400, 1, {"message": "Bad request"}, "error")

@errors_bp.app_errorhandler(404)
def page_not_found(e):
    return sendResponse(404, 1, {"message": "Page not found"}, "error")

@errors_bp.app_errorhandler(405)
def method_not_allowed(e):
    return  sendResponse(405, 3, {"message": "Method Not Allowed"}, "error")

@errors_bp.app_errorhandler(500)
def server_error(e):
    return  sendResponse(500, 2, {"message": "Internal server error"}, "error")