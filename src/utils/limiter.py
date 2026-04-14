import flask_login
from flask_limiter.util import get_remote_address

def get_user_id():
    if flask_login.current_user.is_authenticated:
        return str(flask_login.current_user.id)
    return get_remote_address()