from functools import wraps
from flask import request
from src.utils.response import sendResponse

def checkFileSize(max_length):
    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            fileSize = request.content_length
            if fileSize != None and fileSize > max_length:
                return sendResponse(413, 15010, {"message": "File exceeded max size"}, "error")
            return f(*args, **kwargs)
        return wrapper
    return decorator