from src.models.User_Class import User_Class

def all_user_classes(idUser):
    userClasses = User_Class.query.filter_by(idUser = idUser)
    classes = []

    for cl in userClasses:
        classes.append(cl.idClass)

    return classes