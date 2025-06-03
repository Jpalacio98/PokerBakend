from pypokerengine.api.game import setup_config

from app.game.dealer import Dealer
from app.game.players.apprentice_player import ApprenticePlayer
from app.game.players.casual_player import CasualPlayer
from app.game.players.enthusiast_player import EnthusiastPlayer
from app.game.players.expert_player import ExpertPlayer
from app.game.players.grand_poker_master_player import GrandPokerMasterPlayer
from app.game.players.human_player import HumanPlayer
import random ,time ,eventlet
from faker import Faker

from app.game.players.local_legend_player import LocalLegendPlayer
from app.game.players.national_champion_player import NationalChampionPlayer
from app.game.players.novice_player import NovicePlayer
from app.game.players.poker_legend_player import PokerLegendPlayer
from app.game.players.shark_player import SharkPlayer
from app.extensions import active_rooms



human = None  # Variable global para el jugador humano
config = None
room = None
dealer = None
_shared_app = None

def init_app(app):
    global _shared_app
    _shared_app = app

def get_app():
    if not _shared_app:
        raise RuntimeError("La aplicación Flask no ha sido inicializada")
    return _shared_app
# Definición de niveles y sus clases
levels = [
    {"id": 1, "name": "Novice", "class": NovicePlayer},
    {"id": 2, "name": "Apprentice", "class": ApprenticePlayer},
    {"id": 3, "name": "Enthusiast", "class": EnthusiastPlayer},
    {"id": 4, "name": "Casual Player", "class": CasualPlayer},
    {"id": 5, "name": "Expert Player", "class": ExpertPlayer},
    {"id": 6, "name": "Shark", "class": SharkPlayer},
    {"id": 7, "name": "Local Legend", "class": LocalLegendPlayer},
    {"id": 8, "name": "National Champion", "class": NationalChampionPlayer},
    {"id": 9, "name": "Grand Poker Master", "class": GrandPokerMasterPlayer},
    {"id": 10, "name": "Poker Legend", "class": PokerLegendPlayer},
]
get_level_name = lambda id: next(level["name"] for level in levels if level["id"] == id)
# Función para obtener las probabilidades de selección de bots

def get_level_probabilities(table_level):
    probabilities = {}

    # El 50% de los bots serán del mismo nivel que la mesa
    probabilities[table_level["id"]] = 0.5

    # Distribuir el otro 50% entre los niveles superiores
    remaining_probability = 0.5
    higher_levels = [level for level in levels if level["id"] > table_level["id"]]
    probability_per_level = remaining_probability / len(higher_levels) if higher_levels else 0

    for level in higher_levels:
        probabilities[level["id"]] = probability_per_level

    return probabilities
# Funcion para gener el perfil del bot

def bot_profile():
    fake = Faker()
    gender = random.choice(["male", "female"])  # Selecciona aleatoriamente el género
    first_name = fake.first_name_male() if gender == "male" else fake.first_name_female()
    last_name = fake.last_name()
    
    # Generar una URL de imagen basada en el género
    imagen_url = f"https://randomuser.me/api/portraits/{'men' if gender == 'male' else 'women'}/{random.randint(1, 99)}.jpg"

    return {
        "name": f"{first_name} {last_name}",
        "gender": gender,
        "image": imagen_url
    }
# Función para añadir bots a la mesa

def add_bots_to_table(socketio,table_level, number_of_bots,room_id):
    probabilities = get_level_probabilities(table_level)
    bots = []
    for i in range(number_of_bots):
        random_value = random.random()
        cumulative_probability = 0

        for level_id, probability in probabilities.items():
            cumulative_probability += probability
            if random_value < cumulative_probability:
                # Obtener la clase correspondiente al nivel
                level_class = next(level["class"] for level in levels if level["id"] == level_id)
                # Crear el bot con la clase adecuada
                profile= bot_profile()
                bot = level_class(socketio,profile['name'],profile['image'],room_id)
                bots.append(bot)
                break
    return bots

def add_players(socketio,config,num,level_id,name_human,room_id):
    global human
    human = HumanPlayer(socketio,name_human,None,room_id)
    level_name = next(level["name"] for level in levels if level["id"] == level_id)
    table_level = next(level for level in levels if level["name"] == level_name)
    players = add_bots_to_table(socketio,table_level,num-1,room_id)
    players.append(human)
    random.shuffle(players)
    for player in players:
        config.register_player(name=player.name, algorithm=player)
    return players

def config_game(socketio, table,name_human,room_id):
    global config, room
    room = table['name']
    config = setup_config(max_round=10, initial_stack=table['required_stack'], small_blind_amount=table['small_blind'])
    players = add_players(socketio,config,table['max_players'],table['level_id'],name_human,room_id)
    pl = []
    jumps =7-len(players)
    position = 0
    if jumps > 0: 
        for player in players:
            if jumps > 0 :
                if round(random.random(),1) < .5:
                    position+=1
                    jumps = jumps - 1        
            pl.append({'name':player.name,'level':player.__class__.__name__,'stack':table['required_stack'],'image':player.image, 'pos':position})
            position+=1
    else:
        for player in players:    
            pl.append({'name':player.name,'level':player.__class__.__name__,'stack':table['required_stack'],'image':player.image, 'pos':position})
            position+=1
    return pl

def get_game_instance_for_table(table_id, tables_state):
    """
    Obtiene la instancia del objeto del juego para una mesa específica.
    Esta función es un EJEMPLO, necesitas adaptarla a CÓMO almacenas
    la instancia del juego dentro de tu `game_tables` (por ejemplo, en `table_data['game_instance']`).
    """
    if table_id in tables_state:
        # Asume que la instancia se guarda en la clave 'game_instance'
        return tables_state[table_id].get('game_instance')
    return None

def start_game_poker(socketio, room,user_name):
    result_message =  start_poker(config,socketio,room,user_name)
    return result_message

def start_poker(config, socketio,room,user_name,verbose=2):
    shared_app = get_app()
    if not shared_app:
        raise RuntimeError("shared_app aún no está inicializada")
    global dealer
    config.validation()
    with shared_app.app_context():
        print("game start db")
        active_rooms[room]['userservice'].game_start()
    dealer = Dealer(config.sb_amount, config.initial_stack, config.ante,socketio,user_name,room,shared_app)
    print(dealer.user_name)
    dealer.set_verbose(verbose)
    dealer.set_blind_structure(config.blind_structure)
    for info in config.players_info:
        dealer.register_player(info["name"], info["algorithm"])
    result_message = dealer.start_game(config.max_round)
    with shared_app.app_context():
        print("game stop db")
        active_rooms[room]['userservice'].game_stop()
    
    return _format_result(result_message)



def _format_result(result_message):
    return {
            "rule": result_message["message"]["game_information"]["rule"],
            "players": result_message["message"]["game_information"]["seats"]
            }