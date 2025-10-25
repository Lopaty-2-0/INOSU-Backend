from src.models.User_Team import User_Team
from src.models.Task import Task
from src.models.User import User
from src.models.Team import Team

def all_user_tasks(idUser):
    user_teams = User_Team.query.filter_by(idUser = idUser)
    tasks = []

    for t in user_teams:
        task = Task.query.filter_by(id = t.idTask).first()
        user = User.query.filter_by(id = task.guarantor).first()
        team = Team.query.filter_by(idTeam = t.idTeam, idTask = t.idTask).first()
        guarantor = {"id":user.id, "name":user.name, "surname": user.surname, "abbreviation": user.abbreviation, "createdAt": user.createdAt, "role": user.role.value, "profilePicture":user.profilePicture, "email":user.email, "updatedAt":user.updatedAt}
        tasks.append({"id":t.idTask, "name":task.name, "startDate":task.startDate, "endDate":task.endDate, "task":task.task, "guarantor":guarantor, "status":team.status.value, "elaboration":team.elaboration, "review":team.review})
        
    return tasks