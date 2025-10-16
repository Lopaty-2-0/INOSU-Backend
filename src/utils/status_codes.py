from werkzeug.exceptions import HTTPException

class InsufficientStorage(HTTPException):
    code = 507
    description = "Insufficient Storage"