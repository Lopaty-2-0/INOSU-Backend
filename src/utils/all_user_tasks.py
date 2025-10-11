from src.models.User_Task import User_Task
from src.models.Task import Task
from src.models.User import User

def all_user_tasks(idUser):
    user_tasks = User_Task.query.filter_by(idUser = idUser)
    tasks = []

    for t in user_tasks:
        task = Task.query.filter_by(id = t.idTask).first()
        user = User.query.filter_by(id = task.guarantor).first()
        guarantor = {"id":user.id, "name":user.name, "surname": user.surname, "abbreviation": user.abbreviation, "createdAt": user.createdAt, "role": user.role, "profilePicture":user.profilePicture, "email":user.email}
        tasks.append({"id":t.idTask, "name":task.name, "startDate":task.startDate, "endDate":task.endDate, "task":task.task, "guarantor":guarantor, "status":t.status, "elaboration":t.elaboration, "review":t.review})
        
    return tasks