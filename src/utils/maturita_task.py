from src.models.Team import Team
from src.models.User_Team import User_Team
from src.models.Maturita_Task import Maturita_Task
from src.models.Task import Task
from src.utils.enums import Type, Status
from src.models.Version_Team import Version_Team
from app import db
from src.utils.version import delete_upload_version
from src.utils.task import delete_upload_task


def maturita_task_delete(idUser, idMaturita):
    userTeams = User_Team.query.join(Team, (User_Team.idTeam == Team.idTeam) & (User_Team.idTask == Team.idTask) & (User_Team.guarantor == Team.guarantor)).join(Task, (Team.idTask == Task.id) & (Team.guarantor == Task.guarantor)).join(Maturita_Task, (Maturita_Task.idTask == Task.id) & (Maturita_Task.guarantor == Task.guarantor)).filter(User_Team.idUser == idUser, Task.type == Type.Maturita, Team.status != Status.Approved, Maturita_Task.idMaturita == idMaturita).all()

    for userTeam in userTeams:
        versions = Version_Team.query.filter_by(idTask = userTeam.idTask, idTeam = userTeam.idTeam, guarantor = userTeam.guarantor).all()
        task = Task.query.filter_by(id = userTeam.idTask, guarantor = userTeam.guarantor).first()
        taskFile = task.task

        for version in versions:
            if version.elaboration:
                delete_upload_version(version.idTask, version.idTeam, version.elaboration, version.guarantor, version.idVersion)

        db.session.delete(task)
        db.session.commit()

        delete_upload_task(id = userTeam.idTask, guarantor = userTeam.guarantor, task = taskFile)