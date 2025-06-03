from flask import request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.services.auth_services import register_user, login_user, get_levels
from app.models.user import User
from app import db
from app.utils.decorators import role_required


def register():
    data = request.get_json()

    try:
        token, user = register_user(
            data['username'], data['email'], data['password'], data['fullname'],)
        return jsonify({"message": "Usuario registrado exitosamente", "user_id": user.id,"access_token":token}), 201
    except ValueError as e:
        return jsonify({"error": str(e)}), 400


def login():
    data = request.get_json()
    try:
        access_token, user,player = login_user(data['identifier'], data['password'])
        return jsonify({
            "access_token": access_token,
            "user": {
                "id": user.id,
                "username": user.username,
                "email": user.email,
                "fullname": user.full_name
            },
            "player":{
                "id": player.id,
                "level_id":player.level_id,
                "balance":player.balance,
                "stack":player.stack,
                "total_points":player.total_points
            }
        }), 200
    except ValueError as e:
        return jsonify({"error": str(e)}), 401


def levels():
    try:
        levels = get_levels()
        levels_data = [
            {
                "id": level.id,
                "name":level.name,
                "blind_min":level.blind_min,
                "blind_max":level.blind_max,
                "required_points": level.required_points,
            } for level in levels
        ]
        return jsonify(levels_data), 200
    except ValueError as e:
        return jsonify({"error": str(e)}), 401


@jwt_required()
def profile():
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    return jsonify({"username": user.username, "email": user.email}), 200


@jwt_required()
@role_required('admin')
def assign_role(user_id, role):
    current_user_id = get_jwt_identity()
    current_user = User.query.get(current_user_id)

    # Verificar si el usuario actual es administrador
    if not current_user.has_role('admin'):
        return jsonify({"error": "No tienes permisos para realizar esta acción"}), 403

    user = User.query.get(user_id)
    if not user:
        return jsonify({"error": "Usuario no encontrado"}), 404

    user.role = role
    db.session.commit()
    return jsonify({"message": f"Rol asignado exitosamente: {role}"}), 200
