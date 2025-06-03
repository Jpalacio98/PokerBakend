# app/game/players/apprentice_player.py
import random
import eventlet
from pypokerengine.players import BasePokerPlayer
# Importar funciones desde __init__.py
from . import timeSleep, _card_rank_to_int


class ApprenticePlayer(BasePokerPlayer):
    def __init__(self, socketio, name, image, room_id):
        self.name = name
        self.image = image
        self.socketio = socketio
        self.uuid = None
        self.hole_card = []
        self.game_info = {}
        self.room_id = room_id

    def declare_action(self, valid_actions, hole_card, round_state):
        self.socketio.emit(
            'shift_player', {'name': self.name}, room=self.room_id)
        print(f"--- {self.name} (Apprentice) acting ---")
        eventlet.sleep(timeSleep())  # Usar la función importada

        # --- Identificar acciones válidas ---
        fold_action = next(
            (a for a in valid_actions if a['action'] == 'fold'), None)
        raise_action = next(
            (a for a in valid_actions if a['action'] == 'raise'), None)
        _call_options = [a for a in valid_actions if a['action'] == 'call']
        check_action = next(
            (a for a in _call_options if a['amount'] == 0), None)
        call_action = next((a for a in _call_options if a['amount'] > 0), None)

        street = round_state['street']
        my_hole_card = hole_card
        action_to_take = None
        amount = 0

        # --- Lógica Nivel 2: Evitar manos muy malas pre-flop ---
        is_junk = False
        if street == 'preflop':
            ranks = sorted([_card_rank_to_int(c[1]) for c in my_hole_card],
                           reverse=True) if my_hole_card else [0, 0]
            suits = [c[0] for c in my_hole_card] if my_hole_card else ['', '']
            is_suited = len(suits) > 1 and suits[0] == suits[1]
            if not is_suited:
                if (ranks[0] <= 7) or \
                   (ranks[0] == 8 and ranks[1] <= 3) or \
                   (ranks[0] == 9 and ranks[1] <= 4) or \
                   (ranks[0] == 10 and ranks[1] <= 5):
                    is_junk = True

            if is_junk:
                if fold_action:
                    action_to_take = fold_action
                    print(f"{self.name} folds weak hand preflop: {my_hole_card}")
                elif check_action:
                    action_to_take = check_action
                    print(f"{self.name} checks weak hand preflop: {my_hole_card}")

        # --- Si no es preflop o la mano no es basura (o no pudimos fold/check), jugar aleatorio ---
        if action_to_take is None:
            possible_actions = [
                a for a in valid_actions if a['action'] in ['fold', 'call', 'raise']]
            if not possible_actions:
                action_to_take = random.choice(
                    valid_actions) if valid_actions else None
            else:
                non_fold_actions = [
                    a for a in possible_actions if a['action'] != 'fold']
                if non_fold_actions:
                    action_to_take = random.choice(non_fold_actions)
                else:
                    action_to_take = fold_action

        # --- Calcular Amount para la acción elegida ---
        if action_to_take:
            action_type = action_to_take["action"]
            if action_type == "raise":
                min_raise = action_to_take["amount"]["min"]
                max_raise = action_to_take["amount"]["max"]
                if min_raise == -1:  # Fallback
                    fallback_action = call_action if call_action else check_action if check_action else fold_action
                    action_to_take = fallback_action if fallback_action else action_to_take
                    amount = action_to_take["amount"] if action_to_take and action_to_take['action'] != 'fold' else 0
                elif min_raise >= max_raise:
                    amount = min_raise
                else:
                    amount = random.randint(min_raise, max_raise)
            elif action_type == "call":
                amount = action_to_take["amount"]
            else:
                amount = 0
        else:
            print(f"ERROR: {self.name} no pudo decidir una acción.")
            return "fold", 0

        print(
            f"{self.name} chooses: {action_to_take['action']} {amount if amount > 0 else ''}")
        self.socketio.emit("bot_action", {
                           "player": self.name, "action": action_to_take["action"], "amount": amount}, room=self.room_id)
        return action_to_take["action"], amount

    # ... (receive_* messages iguales que NovicePlayer) ...
    def receive_game_start_message(self, game_info):
        self.game_info = game_info
        seats = game_info['seats']
        if self.uuid == None:
            for seat in seats:
                if seat['name'] == self.name:
                    self.uuid == seat['uuid']
        self.socketio.emit(
            "game_start", {"message": f"{self.name}: El juego ha comenzado"}, room=self.room_id)

    def receive_round_start_message(self, round_count, hole_card, seats):
        self.hole_card = hole_card
        self.was_preflop_aggressor = False
        self.socketio.emit("round_start", {"round_count": round_count, 'seats': seats, 'hole_cards': {
                           'name': self.name, 'cards': hole_card}}, room=self.room_id)

    def receive_street_start_message(self, street, round_state): pass

    def receive_game_update_message(self, action, round_state):
        self.socketio.emit(
            "game_update", {"action": action, "round_state": round_state}, room=self.room_id)

    def receive_round_result_message(
            self, winners, hand_info, round_state):
        win = any(self.name == win['name'] for win in winners)
        if win:
            self.socketio.emit(
                "winners", {"winners": winners}, room=self.room_id)
