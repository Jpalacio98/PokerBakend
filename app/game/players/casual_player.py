# app/game/players/casual_player.py
import random
import eventlet
from pypokerengine.players import BasePokerPlayer
# Importar funciones desde __init__.py
from . import (timeSleep, _get_my_position, _card_rank_to_int,
               _evaluate_postflop_hand_stub)  # No necesita _is_strong_preflop si usamos helper interno


class CasualPlayer(BasePokerPlayer):
    def __init__(self, socketio, name, image,room_id):
        self.name = name
        self.image = image
        self.socketio = socketio
        self.uuid = None
        self.hole_card = []
        self.game_info = {}
        self.room_id=room_id

    # Helper específico para este nivel y superiores
    def _should_play_preflop(self, hole_card, position):
        """Define rangos simples por posición."""
        if not hole_card or len(hole_card) < 2:
            return False
        ranks = sorted([_card_rank_to_int(c[1])
                       for c in hole_card], reverse=True)
        is_pair = ranks[0] == ranks[1]
        is_suited = hole_card[0][0] == hole_card[1][0]

        if position == "early":
            if is_pair and ranks[0] >= 9:
                return True  # 99+
            if ranks[0] == 14 and ranks[1] >= 11:
                return True  # AQ+, AK
            if ranks[0] == 13 and ranks[1] >= 12:
                return True  # KQ
            if is_suited and ranks[0] == 14 and ranks[1] == 10:
                return True  # ATs
            if is_suited and ranks[0] == 13 and ranks[1] == 11:
                return True  # KJs
        elif position == "middle":
            if is_pair and ranks[0] >= 7:
                return True  # 77+
            if ranks[0] >= 12 and ranks[1] >= 11:
                return True  # QJ+
            if ranks[0] == 14 and ranks[1] >= 10:
                return True  # AT+
            if is_suited and ranks[0] >= 11 and ranks[1] >= 9:
                return True  # J9s+, Q9s+, K9s+
            if is_suited and abs(ranks[0] - ranks[1]) == 1 and ranks[0] >= 8:
                return True  # 87s+
        else:  # late
            if is_pair and ranks[0] >= 5:
                return True  # 55+
            if ranks[0] >= 11 and ranks[1] >= 9:
                return True  # J9+
            if ranks[0] == 14 and ranks[1] >= 7:
                return True  # A7+
            if is_suited and ranks[0] >= 10 and ranks[1] >= 7:
                return True  # T7s+
            if is_suited and abs(ranks[0] - ranks[1]) == 1 and ranks[0] >= 6:
                return True  # 65s+
            if not is_suited and ranks[0] >= 12 and ranks[1] >= 10:
                return True  # QTo+
        return False

    def declare_action(self, valid_actions, hole_card, round_state):
        self.socketio.emit('shift_player', {'name': self.name},room=self.room_id)
        print(f"--- {self.name} (Casual) acting ---")
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
        community_card = round_state['community_card']
        action_to_take = None
        amount = 0

        # --- Lógica Nivel 4 ---
        is_premium_hand_preflop = False

        if street == 'preflop':
            position = _get_my_position(round_state, self.uuid)
            print(f"{self.name} Position: {position}")
            should_play = self._should_play_preflop(
                my_hole_card, position)  # Usar helper interno

            ranks = sorted([_card_rank_to_int(c[1]) for c in my_hole_card],
                           reverse=True) if my_hole_card else [0, 0]
            is_pair = ranks[0] == ranks[1]
            is_premium_hand_preflop = (is_pair and ranks[0] >= 12) or (
                ranks[0] == 14 and ranks[1] == 13)

            if should_play:
                raise_prob = 0.8 if is_premium_hand_preflop else 0.4
                if raise_action and random.random() < raise_prob:
                    action_to_take = raise_action
                elif call_action:
                    action_to_take = call_action
                elif check_action:
                    action_to_take = check_action
                elif raise_action:
                    action_to_take = raise_action
                else:
                    action_to_take = fold_action if fold_action else random.choice(
                        valid_actions)
            else:
                if fold_action:
                    action_to_take = fold_action
                elif check_action:
                    action_to_take = check_action
                else:
                    action_to_take = call_action if call_action else random.choice(
                        valid_actions)
        else:  # Flop, Turn, River
            hand_strength = _evaluate_postflop_hand_stub(
                my_hole_card, community_card)
            print(f"{self.name} Postflop Hand Strength ({street}): {hand_strength}")
            is_value_hand = hand_strength in ["TWO_PAIR", "TRIPS_OR_BETTER"]
            is_decent_hand = hand_strength == "PAIR"

            if is_value_hand:
                raise_prob = 0.7
                if raise_action and random.random() < raise_prob:
                    action_to_take = raise_action
                elif call_action:
                    action_to_take = call_action
                elif check_action:
                    action_to_take = check_action
                else:
                    action_to_take = raise_action if raise_action else fold_action
            elif is_decent_hand:
                raise_prob = 0.1
                if raise_action and random.random() < raise_prob:
                    action_to_take = raise_action
                elif call_action:
                    action_to_take = call_action
                elif check_action:
                    action_to_take = check_action
                else:
                    action_to_take = fold_action if fold_action else random.choice(
                        valid_actions)
            else:  # HIGH_CARD
                if check_action:
                    action_to_take = check_action
                elif fold_action:
                    action_to_take = fold_action
                else:
                    action_to_take = call_action if call_action else check_action if check_action else random.choice(
                        valid_actions)

        # --- Calcular Amount ---
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
                    is_value_situation = (street != 'preflop' and is_value_hand) or \
                                         (street == 'preflop' and is_premium_hand_preflop)
                    if is_value_situation:
                        lower_bound = int(
                            min_raise + (max_raise - min_raise) * 0.6)
                        amount = random.randint(
                            max(min_raise, lower_bound), max_raise)
                    else:
                        upper_bound = int(
                            min_raise + (max_raise - min_raise) * 0.6)
                        amount = random.randint(
                            min_raise, max(min_raise, upper_bound))
                    print(
                        f"{self.name} {'Value' if is_value_situation else 'Standard'} raise sizing...")
            elif action_type == "call":
                amount = action_to_take["amount"]
            else:
                amount = 0
        else:
            print(f"ERROR: {self.name} no pudo decidir una acción.")
            return "fold", 0

        # Clamp final amount
        if action_to_take['action'] == 'raise':
            min_r, max_r = action_to_take['amount']['min'], action_to_take['amount']['max']
            if min_r != -1:
                amount = max(min_r, min(amount, max_r))

        print(
            f"{self.name} chooses: {action_to_take['action']} {amount if amount > 0 else ''}")
        self.socketio.emit("bot_action", {
                           "player": self.name, "action": action_to_take["action"], "amount": amount},room=self.room_id)
        return action_to_take["action"], amount

    # ... (receive_* messages iguales que NovicePlayer) ...
    def receive_round_start_message(self, round_count, hole_card, seats):
        self.hole_card = hole_card
        self.socketio.emit(
            "round_start", {"round_count": round_count, 'seats': seats, 'hole_cards': {'name': self.name, 'cards': hole_card}},room=self.room_id)

    def receive_game_start_message(self, game_info):
        self.game_info = game_info
        seats = game_info['seats']
        if self.uuid == None:
            for seat in seats:
                if seat['name'] == self.name:
                    self.uuid == seat['uuid']
        self.socketio.emit(
            "game_start", {"message": f"{self.name}: El juego ha comenzado"},room=self.room_id)

    def receive_round_start_message(self, round_count, hole_card, seats):
        self.hole_card = hole_card
        self.socketio.emit("round_start", {"round_count": round_count, 'seats': seats, 'hole_cards': {
                           'name': self.name, 'cards': hole_card}},room=self.room_id)

    def receive_street_start_message(self, street, round_state): pass
    def receive_game_update_message(self, action, round_state):
        self.socketio.emit(
            "game_update", {"action": action, "round_state": round_state},room=self.room_id)

    def receive_round_result_message(
            self, winners, hand_info, round_state):
        win = any(self.name == win['name'] for win in winners)
        if win:
            self.socketio.emit(
                "winners", {"winners": winners}, room=self.room_id)

