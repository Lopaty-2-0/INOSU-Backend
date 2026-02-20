from flask import Blueprint
from src.route.auth_bp import auth_bp
from src.route.errorhandlers_bp import errors_bp
from src.route.user_bp import user_bp
from src.route.class_bp import class_bp
from src.route.specialization_bp import specialization_bp
from src.route.task_bp import task_bp
from src.route.user_class_bp import user_class_bp
from src.route.user_team_bp import user_team_bp
from src.route.team_bp import team_bp
from src.route.check_file_bp import check_file_bp
from src.route.version_team_bp import version_team_bp
from src.route.topic_bp import topic_bp
from src.route.maturita_bp import maturita_bp
from src.route.maturita_task_bp import maturita_task_bp
from src.route.evaluator_bp import evaluator_bp
from src.route.message_bp import message_bp
from src.route.conversation_bp import conversation_bp
from src.route.event_bp import event_bp

routes_bp = Blueprint("routes", __name__)
routes_bp.register_blueprint(auth_bp)
routes_bp.register_blueprint(errors_bp)
routes_bp.register_blueprint(user_bp)
routes_bp.register_blueprint(class_bp)
routes_bp.register_blueprint(specialization_bp)
routes_bp.register_blueprint(task_bp)
routes_bp.register_blueprint(user_class_bp)
routes_bp.register_blueprint(user_team_bp)
routes_bp.register_blueprint(team_bp)
routes_bp.register_blueprint(check_file_bp)
routes_bp.register_blueprint(version_team_bp)
routes_bp.register_blueprint(topic_bp)
routes_bp.register_blueprint(maturita_bp)
routes_bp.register_blueprint(maturita_task_bp)
routes_bp.register_blueprint(evaluator_bp)
routes_bp.register_blueprint(message_bp)
routes_bp.register_blueprint(conversation_bp)
routes_bp.register_blueprint(event_bp)