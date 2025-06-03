import eventlet


# Aplicar monkey patching al inicio de la aplicación
eventlet.monkey_patch()

from flask_migrate import Migrate

from flask_cors import CORS
from app.models import game, game_history, user, table, table_player,player, level
from app import create_app
from app.extensions import db,socketio


app = create_app()
CORS(app,supports_credentials=True)
migrate = Migrate(app, db)  # Habilita migraciones de base de datos


if __name__ == '__main__':
    socketio.run(app, debug=True,host="0.0.0.0",port=5001)
