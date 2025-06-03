import os

class Config:
    # Configuración de la base de datos
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL', 'mysql+pymysql://root:@localhost/poker')
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Configuración de WebSocket
    SOCKETIO_MESSAGE_QUEUE = os.getenv('SOCKETIO_MESSAGE_QUEUE', 'redis://localhost:6379/0')

    # Configuración de la aplicación
    SECRET_KEY = os.getenv('SECRET_KEY', 'tu_clave_secreta_aqui')
    DEBUG = os.getenv('DEBUG', 'True') == 'True'

    # Configuración de JWT
    JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY', 'tu_clave_secreta_jwt_aqui')
    JWT_ACCESS_TOKEN_EXPIRES = int(os.getenv('JWT_ACCESS_TOKEN_EXPIRES', 3600))  # 1 hora