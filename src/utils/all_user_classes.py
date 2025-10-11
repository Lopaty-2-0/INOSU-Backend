from src.models.User_Class import User_Class

def all_user_classes(idUser):
    user_classes = User_Class.query.filter_by(idUser = idUser)
    classes = []

    for cl in user_classes:
        classes.append(cl.idClass)

    return classes