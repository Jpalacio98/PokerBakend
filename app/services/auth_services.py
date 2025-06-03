from flask_jwt_extended import create_access_token
from app import db
from app.models.user import User
from app.models.level import Level
from app.models.player import Player

def register_user(username, email, password, fullname):
    if User.query.filter_by(username=username).first():
        raise ValueError("El nombre de usuario ya está en uso.")
    if User.query.filter_by(email=email).first():
        raise ValueError("El correo electrónico ya está en uso.")

    user = User(username=username, email=email, full_name=fullname)
    user.set_password(password)
    db.session.add(user)
    db.session.commit()
    player= Player(id=user.id,level_id=1)
    db.session.add(player)
    db.session.commit()
    
    
    access_token = create_access_token(identity=user.id)

    return access_token,user

def login_user(identifier, password):
    """
    Permite iniciar sesión con username o email.
    """
    user = User.query.filter((User.username == identifier) | (User.email == identifier)).first()
    if user is not None:
        player = Player.query.filter(Player.id== user.id).first()
        
    if not user or not user.check_password(password):
        raise ValueError("Nombre de usuario, correo o contraseña incorrectos.")

    # Crear un token JWT
    access_token = create_access_token(identity=user.id)

    return access_token, user,player

def get_levels():
    return Level.query.all()



