from flask import Blueprint
from app.controllers.auth_controllers import register, login, profile,assign_role,levels
#from app.utils.levels_utils import initialize_levels

auth_bp = Blueprint(name='auth',import_name= __name__,url_prefix='/auth')

auth_bp.route('/register', methods=['POST'])(register)
auth_bp.route('/login', methods=['POST'])(login)
auth_bp.route('/get_levels', methods=['GET'])(levels)
auth_bp.route('/profile', methods=['GET'])(profile)
auth_bp.route('/assign_role/<int:user_id>/<string:role>', methods=['POST'])(assign_role)
#auth_bp.route('/initlevels',methods=['GET'])(initialize_levels)