from src.models.User_Team import User_Team
from src.models.Task import Task
from src.models.User import User

def all_user_tasks(idUser):
    user_teams = User_Team.query.filter_by(idUser = idUser)
    tasks = []

    for t in user_teams:
        task = Task.query.filter_by(id = t.idTask).first()
        user = User.query.filter_by(id = task.guarantor).first()
        guarantor = {"id":user.id, "name":user.name, "surname": user.surname, "abbreviation": user.abbreviation, "createdAt": user.createdAt, "role": user.role, "profilePicture":user.profilePicture, "email":user.email, "updatedAt":user.updatedAt}
        tasks.append({"id":t.idTask, "name":task.name, "startDate":task.startDate, "endDate":task.endDate, "task":task.task, "guarantor":guarantor, "status":t.status, "elaboration":t.elaboration, "review":t.review})
        
    return tasks