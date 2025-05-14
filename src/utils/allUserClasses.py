from src.models.User_Class import User_Class

def allUserClasses(idUser):
    user_classes = User_Class.query.filter_by(idUser = idUser)
    classes = []

    for cl in user_classes:
        classes.append(cl.idClass)

    return classes