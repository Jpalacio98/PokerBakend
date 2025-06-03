
from faker import Faker
from app.models.level import Level
from app.models.table import Table
from app.models.user import User
from app.models.player import Player
import random


from app import create_app, db

app = create_app()
def create_levels():
    levels = [
        {"name": "Novice", "blind_min": 1, "blind_max": 10, "required_points": 0},
        {"name": "Apprentice", "blind_min": 5, "blind_max": 20, "required_points": 1000},
        {"name": "Enthusiast", "blind_min": 10, "blind_max": 50, "required_points": 5000},
        {"name": "Casual Player", "blind_min": 25, "blind_max": 100, "required_points": 15000},
        {"name": "Expert Player", "blind_min": 50, "blind_max": 200, "required_points": 50000},
        {"name": "Shark", "blind_min": 100, "blind_max": 500, "required_points": 100000},
        {"name": "Local Legend", "blind_min": 250, "blind_max": 1000, "required_points": 250000},
        {"name": "National Champion", "blind_min": 500, "blind_max": 2000, "required_points": 500000},
        {"name": "Grand Poker Master", "blind_min": 1000, "blind_max": 5000, "required_points": 1000000},
        {"name": "Poker Legend", "blind_min": 2500, "blind_max": 10000, "required_points": 2500000},
    ]

    # Create an app context to work with the database
    with app.app_context():
        for indx, level in enumerate(levels):
            new_level = Level(
                id=indx+1,
                name=level["name"],
                blind_min=level["blind_min"],
                blind_max=level["blind_max"],
                required_points=level["required_points"]
            )
            db.session.add(new_level)
            db.session.commit()
        print("10 levels created successfully!")

# Crear 2 usuarios y 3 mesas por nivel
def create_users_and_tables():
    fake = Faker()

    with app.app_context():
        # Crear 2 usuarios
        users = []
        user = User(
            id=1,
            full_name="Super Admin",
            username="admin",
            email="admin2@admin.com"
        )
        user.set_password("admin")
        db.session.add(user)
        users.append(user)
        for _ in range(2):
            user = User(
                full_name=fake.name(),
                username=fake.user_name(),
                email=fake.email(),
                
            )
            user.set_password("user123")
            db.session.add(user)
            users.append(user)
        
        db.session.commit()
        # Crear 3 mesas por cada nivel
        levels = Level.query.all()  # Asumiendo que ya tienes niveles creados
        for level in levels:
            for _ in range(3):
                table = Table(
                    name=f"Table {fake.company()} {level.name}",
                    blind=random.randint(level.blind_min, level.blind_max),
                    required_stack=random.randint(level.blind_min * 10, level.blind_max * 10),
                    level_id=level.id,
                    max_players=random.randint(3,7),  # Número máximo de jugadores, puedes cambiar esto si lo deseas
                    owner_id=users[random.randint(0, len(users)-1)].id  # Asignar propietario aleatorio
                )
                db.session.add(table)
        
        db.session.commit()
        print("2 users and 3 tables for each level have been created successfully!")
        

def create_players():
    
    with app.app_context():
        users = User.query.all()
        for user in users:
            player= Player(id=user.id,level_id=1)
            db.session.add(player)
        db.session.commit()
    print("Players have been created successfully!")
        
if __name__ == "__main__":
    create_levels()
    create_users_and_tables()
    create_players()
    
        #"Novice","Apprentice","Enthusiast", "Casual Player","Expert Player", "Shark","Local Legend","National Champion","Grand Poker Master","Poker Legend",
    