from flask import Flask

from app.websocket import init_websocket
from app.extensions import db,jwt,socketio


def create_app(config_class='config.default.Config'):
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Inicializar extensiones
    db.init_app(app)
    jwt.init_app(app)
    socketio.init_app(app, cors_allowed_origins="*",async_mode='eventlet')
    init_websocket(socketio)

    # Registrar blueprints
    from app.routes.auth_routes import auth_bp
    from app.routes.table_routes import table_bp


    app.register_blueprint(auth_bp)
    app.register_blueprint(table_bp)
    
    from app.game import engine
    engine.init_app(app)
    
    return app

