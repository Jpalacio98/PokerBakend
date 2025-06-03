from flask import Blueprint

from app.controllers.table_controles import create,update,delete,get_all,get,get_owner

table_bp = Blueprint(name='table',import_name= __name__,url_prefix='/table')
table_bp.route('/new', methods=['POST'])(create)
table_bp.route('/get_all', methods=['GET'])(get_all)
table_bp.route('/get/<int:table_id>', methods=['GET'])(get)
table_bp.route('/get_by_owner/<int:owner_id>', methods=['GET'])(get_owner)
table_bp.route('/update/<int:table_id>', methods=['PUT'])(update)
table_bp.route('/delete/<int:table_id>', methods=['DELETE'])(delete)
