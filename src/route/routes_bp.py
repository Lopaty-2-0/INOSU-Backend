from flask import Blueprint
from src.route.auth_bp import auth_bp
from src.route.errorhandlers_bp import errors_bp
from src.route.user_bp import user_bp
from src.route.class_bp import class_bp
from src.route.specialization_bp import specialization_bp
from src.route.task_bp import task_bp
from src.route.user_class_bp import user_class_bp
from src.route.user_task_bp import user_task_bp
from src.route.task_class_bp import task_class_bp
from src.route.check_file_bp import check_file_bp

routes_bp = Blueprint("routes", __name__)
routes_bp.register_blueprint(auth_bp)
routes_bp.register_blueprint(errors_bp)
routes_bp.register_blueprint(user_bp)
routes_bp.register_blueprint(class_bp)
routes_bp.register_blueprint(specialization_bp)
routes_bp.register_blueprint(task_bp)
routes_bp.register_blueprint(user_class_bp)
routes_bp.register_blueprint(user_task_bp)
routes_bp.register_blueprint(task_class_bp)
routes_bp.register_blueprint(check_file_bp)