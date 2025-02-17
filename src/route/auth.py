from src import app, db
from src.utils.response import sendResponse
from src.models import User

@app.errorhandler(404)
def page_not_found(e):
    return sendResponse(e, , "Page not found", "error")

@app.errorhandler(500)
def server_error(e):
    return sendResponse(e, , "Internal server error", "error")

@app.route("/registration")
def registration(name, surname, abbreviation, role, password, profilePicture, email, idClass):
    if name == None:
        return sendResponse(400, , "Name is not entered", "error")
    if surname == None:
        return sendResponse(400, , "Surname is not entered", "error")
    if role == None:
        return sendResponse(400, , "Role is not entered", "error")
    if password == None:
        return sendResponse(400, , "Password is not entered", "error")
    if len(str(password)) < 5:
        return sendResponse(400, , "Password is too short", "error")
    if email == None:
        return sendResponse(400, , "Email is not entered", "error")
    
    if db.Query.filter_by(email = email) == email
    newUser = User(name = name, surname = surname, abbreviation = abbreviation, role = role, password = password, profilePicture = profilePicture, email = email, idClass = idClass)

    db.session.add(newUser)
    db.session.commit()

@app.route("/login")
def login(login, password):
    if login == None or password == None:
        return sendResponse(400, , "Email or password not entered", "error")
    
