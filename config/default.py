import os

class Config:
    # Configuración de la base de datos
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL', 'postgresql://poker_1i73_user:uJDfmxjpjJHT0h3dKC9h6WTGRYaWiSYd@dpg-d2kdavali9vc73e7nj4g-a/poker_1i73')
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Configuración de WebSocket
    SOCKETIO_MESSAGE_QUEUE = os.getenv('SOCKETIO_MESSAGE_QUEUE', 'redis://localhost:6379/0')

    # Configuración de la aplicación
    SECRET_KEY = os.getenv('SECRET_KEY', '^YXjotrXfbHX')
    DEBUG = os.getenv('DEBUG', 'True') == 'True'

    # Configuración de JWT
    JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY', '^YXjotrXfbHX')
    JWT_ACCESS_TOKEN_EXPIRES = int(os.getenv('JWT_ACCESS_TOKEN_EXPIRES', 3600))  # 1 hora