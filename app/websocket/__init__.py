
from .handlers import setup_websocket_events

def init_websocket(socketio):
    setup_websocket_events(socketio)
