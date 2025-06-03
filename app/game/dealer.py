import random
from collections import OrderedDict
from threading import Event
from pypokerengine.engine.poker_constants import PokerConstants as Const
from pypokerengine.engine.table import Table
from pypokerengine.engine.player import Player
from pypokerengine.engine.round_manager import RoundManager
from pypokerengine.engine.message_builder import MessageBuilder
from app.extensions import active_rooms





class Dealer:

    def __init__(self, small_blind_amount=None, initial_stack=None, ante=None, socketio=None, user_name=None, room=None, app=None):
        self.small_blind_amount = small_blind_amount
        self.ante = ante if ante else 0
        self.initial_stack = initial_stack
        self.uuid_list = self.__generate_uuid_list()
        self.message_handler = MessageHandler()
        self.message_summarizer = MessageSummarizer(verbose=0,socketio=socketio,room=room)
        self.table = Table()
        self.blind_structure = {}
        self.socketio = socketio
        self.user_name = user_name
        self.user_uid = None
        self.room = room
        self.action_event = Event()
        self.game_event = Event()
        self.starter_game_event = Event()
        self.starter_round_event = Event()
        self.game_data ={}
        self.app = app

    def register_player(self, player_name, algorithm):
        self.__config_check()
        uuid = self.__escort_player_to_table(player_name)
        if self.user_name == player_name:
            self.user_uid= uuid
        algorithm.set_uuid(uuid)
        self.__register_algorithm_to_message_handler(uuid, algorithm)

    def set_verbose(self, verbose):
        self.message_summarizer.verbose = verbose

    def start_game(self, max_round):
        table = self.table
        self.__notify_game_start(max_round)
        ante, sb_amount = self.ante, self.small_blind_amount
        self.socketio.emit("game_starter",{'message':"¡Bienvenidos a la mesa!",'type':"game"},room= self.room)
        self.starter_game_event.wait()
        self.starter_game_event.clear()
        for round_count in range(1, max_round+1):
            
            ante, sb_amount = self.__update_forced_bet_amount(
                ante, sb_amount, round_count, self.blind_structure)
            table = self.__exclude_short_of_money_players(
                table, ante, sb_amount)
            user_no_stack = self.check_user_stack(table.seats.players)
            
            print(f"el usuario tiene stack: {user_no_stack}")
            if user_no_stack == False:
                
                with self.app.app_context():
                    active_rooms[self.room]['userservice'].game_stop()
                self.socketio.emit("game_option",{'message':"Game Over",'quet':"Quieres iniciar una nueva Patida"},room= self.room)
                self.game_event.wait()
                self.game_event.clear()
                break
            if self.__is_game_finished(table):
                with self.app.app_context():
                    
                    active_rooms[self.room]['userservice'].game_stop()
                self.socketio.emit("game_option",{'message':"Congratulations",'quet':"Quieres iniciar una nueva Patida","seats":table.seats.serialize()},room= self.room)
                self.game_event.wait()
                self.game_event.clear()
                break
            self.socketio.emit("game_starter",{'message':f"Ronda {round_count} comienza. ¡Buena suerte!",'type':"round"},room= self.room)
            self.starter_round_event.wait()
            self.starter_round_event.clear()
            table = self.play_round(round_count, sb_amount, ante, table)
            table.shift_dealer_btn()
        with self.app.app_context():
            active_rooms[self.room]['userservice'].game_stop()
        self.socketio.emit("game_option",{'message':"Game Finished",'quet':"Quieres iniciar una nueva Patida","seats":table.seats.serialize()},room= self.room)
        
        # no olviddes evaluar en que posision quedo en jugador                
        self.game_event.wait()
        self.game_event.clear()
        return self.__generate_game_result(max_round, table.seats)

    def play_round(self, round_count, blind_amount, ante, table):
        state, msgs = RoundManager.start_new_round(
            round_count, blind_amount, ante, table)
        while True:
            self.__message_check(msgs, state["street"])
            if state["street"] != Const.Street.FINISHED:  # continue the round
                action, bet_amount = self.__publish_messages(msgs)
                state, msgs = RoundManager.apply_action(
                    state, action, bet_amount)
      
            else:  # finish the round after publish round result
                self.__publish_messages(msgs)
                self.set_round_data_db(msgs)
                self.set_game_data_db(msgs)
                # esperamos la respuesta del servidor para continuar la ronda
                self.action_event.wait()
                self.action_event.clear()
                break
        return state["table"]

    def set_game_data_db(self,msgs):
        result,data = self.get_game_data(msgs,self.user_uid)
        if data != None:
            data['player']=self.user_name
            with self.app.app_context():
                active_rooms[self.room]['userservice'].add_game_history(result,data)
            
            
    
    def get_game_data(self,msmg,p_uuid):
        # 1. buscamos round result
        for msg in msmg:
            _, data = msg
            #2. validamos que se encuente al final de la partida
            if "round_result_message" == data['message']['message_type']:
                rst =data['message']['round_state']
                winners = data['message']['winners']
                round = rst['round_count']
                pot = rst['pot']['main']['amount']
                street = rst['street']
                finaly_street = [street for street, actions in data['message']['round_state']['action_histories'].items()][-1:]
                p_user = next((p for p in rst['seats'] if p['uuid'] == p_uuid), None)
                # 3.  validamos que el usuario este participando en la partida
                if p_user != None and p_user['state'] != 'folded':
                    if p_uuid == winners[0]['uuid']:
                        result = "Win"
                    else:
                        result = "loss"
                else:
                    result = "leave"
                return result ,{'round':round,'street':street,'pot':pot,'finaly_street':finaly_street}
        return None, None
    
    
    def set_round_data_db(self,msgs):
        data = self.get_round_data(msgs,self.user_uid)
        if len(data) != 0:
            with self.app.app_context():
                for item in data:
                    item['player']=self.user_name
                    active_rooms[self.room]['userservice'].add_round_history(item)

    def get_round_data(self,msmg,p_uuid):
        # 1. buscamos round result
        actions_data = []
        for _, data in msmg:
            msg = data['message']
            if msg['message_type'] == 'round_result_message':
                rst = msg['round_state']
                round_count = rst['round_count']
                for street, actions in rst['action_histories'].items():
                    item = next((r for r in actions if r.get('uuid') == p_uuid), None)
                    if item:
                        
                        action = item['action']
                        bet = item['amount'] if action in {'SMALLBLIND', 'BIGBLIND'} else item['paid'] if action != 'FOLD' else 0
                        actions_data.append({
                            'round': round_count,
                            'street': street,
                            'action': action,
                            'bet': bet
                            
                        })

        return actions_data
    
    def check_user_stack(self,playeres):
      user_has_stack = True
      print(f"check user:  { self.user_name}")
      for player in playeres:
        
        print(f"{player.name}: {player.stack}")
        if player.name == self.user_name and player.stack == 0:
          print(f"{player.name}: {player.stack}")
          user_has_stack = False
          
      return user_has_stack
          
    def starter_game(self):
        self.starter_game_event.set()
        
    def starter_round(self):
        self.starter_round_event.set()
    
    def next_round(self):
        self.action_event.set()
    
    def next_game(self):
        self.game_event.set()
        
    def set_small_blind_amount(self, amount):
        self.small_blind_amount = amount

    def set_initial_stack(self, amount):
        self.initial_stack = amount

    def set_blind_structure(self, blind_structure):
        self.blind_structure = blind_structure

    def __update_forced_bet_amount(self, ante, sb_amount, round_count, blind_structure):
        if round_count in blind_structure:
            update_info = blind_structure[round_count]
            msg = self.message_summarizer.summairze_blind_level_update(
                round_count, ante, update_info["ante"], sb_amount, update_info["small_blind"])
            self.message_summarizer.print_message(msg)
            ante, sb_amount = update_info["ante"], update_info["small_blind"]
        return ante, sb_amount

    def __register_algorithm_to_message_handler(self, uuid, algorithm):
        self.message_handler.register_algorithm(uuid, algorithm)

    def __escort_player_to_table(self, player_name):
        uuid = self.__fetch_uuid()
        player = Player(uuid, self.initial_stack, player_name)
        self.table.seats.sitdown(player)
        return uuid

    def __notify_game_start(self, max_round):
        config = self.__gen_config(max_round)
        start_msg = MessageBuilder.build_game_start_message(
            config, self.table.seats)
        self.message_handler.process_message(-1, start_msg)
        self.message_summarizer.summarize(start_msg)

    def __is_game_finished(self, table):
        return len([player for player in table.seats.players if player.is_active()]) == 1

    def __message_check(self, msgs, street):
        address, msg = msgs[-1]
        invalid = msg["type"] != 'ask'
        invalid &= street != Const.Street.FINISHED or msg["message"]["message_type"] == 'round_result'
        if invalid:
            raise Exception("Last message is not ask type. : %s" % msgs)

    def __publish_messages(self, msgs):
        for address, msg in msgs[:-1]:
            self.message_handler.process_message(address, msg)
        self.message_summarizer.summarize_messages(msgs)
        return self.message_handler.process_message(*msgs[-1])

    def __exclude_short_of_money_players(self, table, ante, sb_amount):
        sb_pos, bb_pos = self.__steal_money_from_poor_player(
            table, ante, sb_amount)
        self.__disable_no_money_player(table.seats.players)
        table.set_blind_pos(sb_pos, bb_pos)
        if table.seats.players[table.dealer_btn].stack == 0:
            table.shift_dealer_btn()
        return table

    def __steal_money_from_poor_player(self, table, ante, sb_amount):
        players = table.seats.players
        # exclude player who cannot pay ante
        for player in [p for p in players if p.stack < ante]:
            player.stack = 0
        if players[table.dealer_btn].stack == 0:
            table.shift_dealer_btn()

        search_targets = players + players + players
        search_targets = search_targets[table.dealer_btn +
                                        1:table.dealer_btn+1+len(players)]
        # exclude player who cannot pay small blind
        sb_player = self.__find_first_elligible_player(
            search_targets, sb_amount + ante)
        sb_relative_pos = search_targets.index(sb_player)
        for player in search_targets[:sb_relative_pos]:
            player.stack = 0
        # exclude player who cannot pay big blind
        search_targets = search_targets[sb_relative_pos +
                                        1:sb_relative_pos+len(players)]
        bb_player = self.__find_first_elligible_player(
            search_targets, sb_amount*2 + ante, sb_player)
        if sb_player == bb_player:  # no one can pay big blind. So steal money from all players except small blind
            for player in [p for p in players if p != bb_player]:
                player.stack = 0
        else:
            bb_relative_pos = search_targets.index(bb_player)
            for player in search_targets[:bb_relative_pos]:
                player.stack = 0
        return players.index(sb_player), players.index(bb_player)

    def __find_first_elligible_player(self, players, need_amount, default=None):
        if default:
            return next((player for player in players if player.stack >= need_amount), default)
        return next((player for player in players if player.stack >= need_amount))

    def __disable_no_money_player(self, players):
        no_money_players = [player for player in players if player.stack == 0]
        for player in no_money_players:
            player.pay_info.update_to_fold()

    def __generate_game_result(self, max_round, seats):
        config = self.__gen_config(max_round)
        result_message = MessageBuilder.build_game_result_message(
            config, seats)
        self.message_summarizer.summarize(result_message)
        return result_message

    def __gen_config(self, max_round):
        return {
            "initial_stack": self.initial_stack,
            "max_round": max_round,
            "small_blind_amount": self.small_blind_amount,
            "ante": self.ante,
            "blind_structure": self.blind_structure
        }

    def __config_check(self):
        if self.small_blind_amount is None:
            raise Exception("small_blind_amount is not set!!\
          You need to call 'dealer.set_small_blind_amount' before.")
        if self.initial_stack is None:
            raise Exception("initial_stack is not set!!\
          You need to call 'dealer.set_initial_stack' before.")

    def __fetch_uuid(self):
        return self.uuid_list.pop()

    def __generate_uuid_list(self):
        return [self.__generate_uuid() for _ in range(100)]

    def __generate_uuid(self):
        uuid_size = 22
        chars = [chr(code) for code in range(97, 123)]
        return "".join([random.choice(chars) for _ in range(uuid_size)])


class MessageHandler:

    def __init__(self):
        self.algo_owner_map = {}

    def register_algorithm(self, uuid, algorithm):
        self.algo_owner_map[uuid] = algorithm

    def process_message(self, address, msg):
        receivers = self.__fetch_receivers(address)
        for receiver in receivers:
            if msg["type"] == 'ask':
                return receiver.respond_to_ask(msg["message"])
            elif msg["type"] == 'notification':
                receiver.receive_notification(msg["message"])
            else:
                raise ValueError(
                    "Received unexpected message which type is [%s]" % msg["type"])

    def __fetch_receivers(self, address):
        if address == -1:
            return self.algo_owner_map.values()
        else:
            if address not in self.algo_owner_map:
                raise ValueError(
                    "Received message its address [%s] is unknown" % address)
            return [self.algo_owner_map[address]]


class MessageSummarizer(object):

    def __init__(self, verbose,socketio=None,room=None):
        self.verbose = verbose
        self.socketio = socketio
        self.room = room

    def print_message(self, message):
        print(message)

    def summarize_messages(self, raw_messages):
        if self.verbose == 0:
            return

        summaries = [self.summarize(raw_message[1])
                     for raw_message in raw_messages]
        summaries = [summary for summary in summaries if summary is not None]
        summaries = list(OrderedDict.fromkeys(summaries))
        for summary in summaries:
            self.print_message(summary)

    def summarize(self, message):
        if self.verbose == 0:
            return None

        content = message["message"]
        message_type = content["message_type"]
        if MessageBuilder.GAME_START_MESSAGE == message_type:
            return self.summarize_game_start(content)
        if MessageBuilder.ROUND_START_MESSAGE == message_type:
            return self.summarize_round_start(content)
        if MessageBuilder.STREET_START_MESSAGE == message_type:
            return self.summarize_street_start(content)
        if MessageBuilder.GAME_UPDATE_MESSAGE == message_type:
            return self.summarize_player_action(content)
        if MessageBuilder.ROUND_RESULT_MESSAGE == message_type:
            return self.summarize_round_result(content)
        if MessageBuilder.GAME_RESULT_MESSAGE == message_type:
            return self.summarize_game_result(content)

    def summarize_game_start(self, message):
        base = "Started the game with player %s for %d round. (start stack=%s, small blind=%s)"
        names = [player["name"]
                 for player in message["game_information"]["seats"]]
        rule = message["game_information"]["rule"]
        return base % (names, rule["max_round"], rule["initial_stack"], rule["small_blind_amount"])

    def summarize_round_start(self, message):
        base = "Started the round %d"
        return base % message["round_count"]

    def summarize_street_start(self, message):
        base = 'Street "%s" started. (community card = %s)'
        return base % (message["street"], message["round_state"]["community_card"])

    def summarize_player_action(self, message):
        base = '"%s" declared "%s:%s"'
        players = message["round_state"]["seats"]
        action = message["action"]
        player_name = [player["name"]
                       for player in players if player["uuid"] == action["player_uuid"]][0]
        return base % (player_name, action["action"], action["amount"])

    def summarize_round_result(self, message):
        base = '"%s" won the round %d (stack = %s)'
        winners = [player["name"] for player in message["winners"]]
        stack = {player["name"]: player["stack"]
                 for player in message["round_state"]["seats"]}
        print(f"winners: {winners}")
        return base % (winners, message["round_count"], stack)

    def summarize_game_result(self, message):
        base = 'Game finished. (stack = %s)'
        stack = {player["name"]: player["stack"]
                 for player in message["game_information"]["seats"]}
        return base % stack

    def summairze_blind_level_update(self, round_count, old_ante, new_ante, old_sb_amount, new_sb_amount):
        base = 'Blind level update at round-%d : Ante %s -> %s, SmallBlind %s -> %s'
        return base % (round_count, old_ante, new_ante, old_sb_amount, new_sb_amount)
