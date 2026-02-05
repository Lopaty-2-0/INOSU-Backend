from src.models.Task import Task
from src.models.User import User
from src.models.User_Team import User_Team
from src.utils.send_email import send_email
from src.email.templates.reminder import email_reminder
from app import scheduler, app
from datetime import timedelta, datetime


def reminder(idTask, idUser, guarantor):
    with app.app_context():
        task = Task.query.filter_by(id = idTask, guarantor = guarantor).first()
        user = User.query.filter_by(id = idUser).first()
        userTeam = User_Team.query.filter_by(idUser = idUser, idTask = idTask, guarantor = guarantor).first()

        if not task or not user or not userTeam or not user.reminders:
            return
        
        text = "Upozornění uzavírky události" + task.name
        
        send_email(user.email, "Reminder", email_reminder(name = user.name + " " + user.surname, task_datetime = task.endDate.strftime("%d.%m.%Y %H:%M:%S"), task_name = task.name), text)
    
def cancel_reminder(idUser, idTask, guarantor):
    with app.app_context():
        jobId = f"reminder_{idUser}_{idTask}_{guarantor}"

        try:
            scheduler.remove_job(jobId)
        except:
            pass

def create_reminder(idUser, idTask, guarantor):
    if Task.query.filter_by(id = idTask, guarantor = guarantor).first().endDate - timedelta(days = 1) < datetime.now():
        reminder(idTask = idTask, idUser = idUser, guarantor = guarantor)
        return

    with app.app_context():
        jobId = f"reminder_{idUser}_{idTask}_{guarantor}"

        scheduler.add_job(
            reminder,
            trigger="date",
            run_date=Task.query.filter_by(id = idTask).first().endDate - timedelta(days = 1),
            args=[idTask, idUser, guarantor],
            id=jobId,
            replace_existing=True
        )