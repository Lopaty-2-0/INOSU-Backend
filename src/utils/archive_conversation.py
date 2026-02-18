from src.models.Task import Task
from src.models.Conversation import Conversation
from app import scheduler, app, db
from datetime import timedelta, datetime
from src.utils.enums import Type


def archive_conversation(idTask, idConversation, guarantor):
    with app.app_context():
        task = Task.query.filter_by(id = idTask, guarantor = guarantor).first()
        conversation = Conversation.query.filter_by(idConversation = idConversation, idTask = idTask, guarantor = guarantor).first()
        
        if not conversation or not task or task.type != Type.Maturita:
            return
        
        conversation.isArchived = True
        db.session.commit()
        
def cancel_archive_conversation(idConversation, idTask, guarantor):
    with app.app_context():
        jobId = f"archive_conversation_{idConversation}_{idTask}_{guarantor}"

        try:
            scheduler.remove_job(jobId)
        except:
            pass

def create_archive_conversation(idConversation, idTask, guarantor):
    task = Task.query.filter_by(id = idTask, guarantor = guarantor).first()

    if not task or task.type != Type.Maturita:
        return
    
    if task.endDate - timedelta(days = 1) < datetime.now():
        archive_conversation(idTask = idTask, idConversation = idConversation, guarantor = guarantor)
        return

    with app.app_context():
        jobId = f"archive_conversation_{idConversation}_{idTask}_{guarantor}"

        scheduler.add_job(
            archive_conversation,
            trigger="date",
            run_date=Task.query.filter_by(id = idTask).first().endDate,
            args=[idTask, idConversation, guarantor],
            id=jobId,
            replace_existing=True
        )