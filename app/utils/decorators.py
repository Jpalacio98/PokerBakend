from functools import wraps
from flask_jwt_extended import get_jwt_identity
from flask import jsonify
from app.models.user import User
from flask_socketio import emit

def role_required(role_name):
    def decorator(f):
        @wraps(f)
        def wrapped(*args, **kwargs):
            user_id = get_jwt_identity()
            user = User.query.get(user_id)
            if not user or not user.has_role(role_name):
                return jsonify({"error": "No tienes permisos para realizar esta acción"}), 403
            return f(*args, **kwargs)
        return wrapped
    return decorator


def socket_role_required(role_name):
    def decorator(f):
        @wraps(f)
        def wrapped(*args, **kwargs):
            user_id = get_jwt_identity()
            user = User.query.get(user_id)
            if not user or not user.has_role(role_name):
                emit('error', {'message': 'No tienes permisos para realizar esta acción'})
                return False  # Rechazar el evento
            return f(*args, **kwargs)
        return wrapped
    return decorator
