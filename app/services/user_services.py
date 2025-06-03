from app.models import Game
from app.models.game_history import GameHistory
from app.models.player import Player
from app.models.round_history import RoundHistory
from app.extensions import db
from datetime import datetime

from app.models.user import User

class UserService():
    def __init__(self):
        self.game_id = None
        self.pid = None
        self.table_stack=None
    
    def create_game(self,table_id):
        """
        Crea un nuevo registro de partida usando SQLAlchemy.

        :param table_id: El identificador de la mesa.
        :return: El ID de la partida creada (UUID) o None si falla.
        """
        try:
            # El ID y created_at se manejarán por los 'default' del modelo
            new_game = Game(table_id=table_id)
            db.session.add(new_game)
            db.session.commit()
            print(f"Partida creada con ID: {new_game.id} para la mesa: {table_id}")
            self.game_id = new_game.id
            return new_game.id
        except Exception as e: # Sé más específico con las excepciones de SQLAlchemy si es necesario
            db.session.rollback()
            print(f"Error al crear la partida: {e}")
            return None
    
    def pay_stack(self, table,name):
        self.p_id = self.get_user_id(name)
        player = Player.query.get(self.p_id)
        if player.deduct_balance_for_table(table):
            # proceder a unir al jugador a la mesa
            self.table_stack = table['required_stack']
            db.session.commit()
        else:
            # mostrar error o notificar que no tiene fondos
            pass
    def game_start(self):
        """
        Establece la fecha y hora de inicio para una partida usando SQLAlchemy.

        :param game_id: El ID de la partida a actualizar.
        :return: True si la actualización fue exitosa, False en caso contrario.
        """
        try:
            print(self.game_id)
            game = db.session.get(Game,self.game_id) # Método recomendado en SQLAlchemy 2.0+
            # game = Game.query.get(game_id) # Para versiones anteriores de SQLAlchemy
            print(game)
            
            if not game:
                print(f"No se encontró la partida con ID: {self.game_id} para iniciar.")
                return False
            
            game.start_time = datetime.utcnow() # O datetime.datetime.now() si prefieres hora local
            db.session.commit()
            print(f"Partida {self.game_id} marcada como iniciada a las {game.start_time}.")
            return True
        except Exception as e:
            db.session.rollback()
            print(f"Error al establecer la hora de inicio de la partida {self.game_id}: {e}")
            return False
    
    def game_stop(self):
        """
        Establece la fecha y hora de finalización para una partida usando SQLAlchemy.

        :param game_id: El ID de la partida a actualizar.
        :return: True si la actualización fue exitosa, False en caso contrario.
        """
        try:
            game = db.session.get(Game, self.game_id)
            # game = Game.query.get(game_id) # Para versiones anteriores

            if not game:
                print(f"No se encontró la partida con ID: {self.game_id} para finalizar.")
                return False

            game.end_time = datetime.utcnow()
            gh = GameHistory()
            #1 busca las los registros pertenecientes a self.game_id y añdadelos al rounds:
            #Suma los pot de cada rounds y asignalo en cash
            rounds = gh.query.filter_by(game_id=self.game_id).all()
            print(f"rondas: {rounds}")
            total_cash = sum(r.pot for r in rounds if r.pot is not None)
            print(f"dinero todal de la partida: {total_cash}")
            player = Player.query.get(self.p_id)
            player.set_balance(total_cash,self.table_stack)
            
            db.session.commit()
            print(f"Partida {self.game_id} marcada como finalizada a las {game.end_time}.")
            return True
        except Exception as e:
            db.session.rollback()
            print(f"Error al establecer la hora de finalización de la partida {self.game_id}: {e}")
            return False
    
    def get_user_id(self, username):
        
        user = User.query.filter_by(full_name=username).first()
        if user:
           return user.id
        else:
            None

    def add_game_history(self,result,data):
        try:
            self.p_id = self.get_user_id(data['player'])
            if self.p_id:
                data['result']=result
                pointer = GamePoints()
                new = GameHistory()
                new.game_id= self.game_id
                new.player_id = self.p_id
                new.round =data['round']
                new.result= result
                new.pot =data['pot']
                new.points=pointer.point_eval(data)
                new.street=data['street']
                
                
                
                
                db.session.add(new)
                db.session.commit()
                
                player = Player.query.get(self.p_id)
                player.update_points_and_level(new.points)
                db.session.commit()

                print(f"Resultado de la ronda {new.round}: {result} para el juego : {new.id}")
                return True
            else:
                print(f"el jugador {data['player']} no se encontro en la base de datos")
                return False
        except Exception as e:
            db.session.rollback()
            print(f"Error al establecer la hora de inicio de la partida {self.game_id}: {e}")
            return False
        
    
    def add_round_history(self,data):
        try:
            self.p_id = self.get_user_id(data['player'])
            if self.p_id:
        
                new = RoundHistory()
                new.game_id= self.game_id
                new.player_id = self.p_id
                new.round =data['round']
                new.bet= data['bet']
                new.action =data['action']
                new.street=data['street']
                
                db.session.add(new)
                db.session.commit()
                return True
            else:
                print(f"el jugador {data['player']} no se encontro en la base de datos")
                return False
        except Exception as e:
            db.session.rollback()
            print(f"Error al establecer la hora de inicio de la partida {self.game_id}: {e}")
            return False
    

    
    
class GamePoints:
    def __init__(self):
        self.streets_order = ['preflop', 'flop', 'turn', 'river']

    def point_eval(self, data: dict) -> int:
        """
        Evalúa los puntos basados en la participación, resultado y pot.
        """
        result = data.get("result")
        street = data.get("finaly_street")
        pot = data.get("pot", 0)

        points = 0

        # Puntos por participación según la calle alcanzada
        points += self.points_for_participation(street)

        # Puntos por resultado
        if result == "Win":
            points += self.point_x_game_win()
        elif result == "Loss":
            points += self.point_x_game_loss()
        elif result == "Leave":
            if street == "preflop":
                points += self.penalty_for_fold()

        # Bonus por pot
        points += self.extra_points_for_pot(pot)

        return points

    def points_for_participation(self, street: str) -> int:
        try:
            idx = self.streets_order.index(street)
            return idx + 1  # Preflop=1, Flop=2, Turn=3, River=4
        except ValueError:
            return 0

    def point_x_game_win(self) -> int:
        return 10

    def point_x_game_loss(self) -> int:
        return -5

    def penalty_for_fold(self) -> int:
        return -3

    def extra_points_for_pot(self, pot: int) -> int:
        return min(pot // 100, 10)
