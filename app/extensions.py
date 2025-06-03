from flask_sqlalchemy import SQLAlchemy
from flask_jwt_extended import JWTManager
from flask_socketio import SocketIO

db = SQLAlchemy()
socketio = SocketIO()
jwt = JWTManager()
active_rooms = {}
