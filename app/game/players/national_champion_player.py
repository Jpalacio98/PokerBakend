# app/game/players/national_champion_player.py
import random
import eventlet
from pypokerengine.players import BasePokerPlayer
# Importar funciones desde __init__.py
from . import (timeSleep, _get_my_position, _card_rank_to_int,
               _evaluate_postflop_hand_stub, _has_strong_draw_stub,
               _get_pot_size, _get_active_players_count, _get_my_stack)


class NationalChampionPlayer(BasePokerPlayer):
    def __init__(self, socketio, name, image,room_id):
        self.name = name
        self.image = image
        self.socketio = socketio
        self.uuid = None
        self.hole_card = []
        self.game_info = {}
        self.was_preflop_aggressor = False
        self.room_id=room_id

    # Reutilizar helpers de LocalLegend
    def _is_premium_preflop(self, hole_card):
        if not hole_card or len(hole_card) < 2:
            return False
        ranks = sorted([_card_rank_to_int(c[1])
                       for c in hole_card], reverse=True)
        is_pair = ranks[0] == ranks[1]
        return (is_pair and ranks[0] >= 12) or (ranks[0] == 14 and ranks[1] == 13)

    def _is_speculative_preflop(self, hole_card):
        if not hole_card or len(hole_card) < 2:
            return False
        ranks = sorted([_card_rank_to_int(c[1])
                       for c in hole_card], reverse=True)
        is_suited = hole_card[0][0] == hole_card[1][0]
        is_connected = abs(ranks[0] - ranks[1]) <= 2
        is_pair = ranks[0] == ranks[1]
        return (is_suited and is_connected and ranks[0] < 11) or (is_pair and ranks[0] < 7)

    def _should_play_preflop_adjusted(self, hole_card, position, facing_raise, limpers):
        # (Misma lógica que LocalLegend)
        base_play = self._should_play_preflop_base(hole_card, position)
        if facing_raise:
            if self._is_premium_preflop(hole_card):
                return True
            if (_card_rank_to_int(hole_card[0][1]) == 14 and _card_rank_to_int(hole_card[1][1]) >= 12) or \
               (_card_rank_to_int(hole_card[0][1]) >= 10 and _card_rank_to_int(hole_card[1][1]) >= 10 and hole_card[0][1] == hole_card[1][1]):
                return random.random() < 0.7
            return False
        elif limpers >= 2:
            if base_play:
                return True
            if self._is_speculative_preflop(hole_card) and random.random() < 0.4:
                return True
            return False
        else:
            return base_play

    def _should_play_preflop_base(self, hole_card, position):
        # (Misma lógica que LocalLegend)
        if not hole_card or len(hole_card) < 2:
            return False
        ranks = sorted([_card_rank_to_int(c[1])
                       for c in hole_card], reverse=True)
        is_pair = ranks[0] == ranks[1]
        is_suited = hole_card[0][0] == hole_card[1][0]
        if position == "early":
            if is_pair and ranks[0] >= 9:
                return True
            if ranks[0] == 14 and ranks[1] >= 11:
                return True
            if ranks[0] == 13 and ranks[1] >= 12:
                return True
            if is_suited and ranks[0] == 14 and ranks[1] == 10:
                return True
            if is_suited and ranks[0] == 13 and ranks[1] == 11:
                return True
        elif position == "middle":
            if is_pair and ranks[0] >= 7:
                return True
            if ranks[0] >= 12 and ranks[1] >= 11:
                return True
            if ranks[0] == 14 and ranks[1] >= 10:
                return True
            if is_suited and ranks[0] >= 11 and ranks[1] >= 9:
                return True
            if is_suited and abs(ranks[0] - ranks[1]) == 1 and ranks[0] >= 8:
                return True
        else:  # late
            if is_pair and ranks[0] >= 5:
                return True
            if ranks[0] >= 11 and ranks[1] >= 9:
                return True
            if ranks[0] == 14 and ranks[1] >= 7:
                return True
            if is_suited and ranks[0] >= 10 and ranks[1] >= 7:
                return True
            if is_suited and abs(ranks[0] - ranks[1]) == 1 and ranks[0] >= 6:
                return True
            if not is_suited and ranks[0] >= 12 and ranks[1] >= 10:
                return True
        return False

    def _get_push_fold_range(self, hole_card):
        """Define un rango simple de push/fold (¡Simplificado!)."""
        if not hole_card or len(hole_card) < 2:
            return False
        ranks = sorted([_card_rank_to_int(c[1])
                       for c in hole_card], reverse=True)
        is_pair = ranks[0] == ranks[1]
        is_suited = hole_card[0][0] == hole_card[1][0]
        # Ejemplo de rango (necesita ajuste basado en posición, BBs exactas)
        if is_pair and ranks[0] >= 5:
            return True  # 55+
        if ranks[0] == 14 and ranks[1] >= 2:
            return True  # Ax+
        if ranks[0] == 13 and ranks[1] >= 7:
            return True  # K7+
        if ranks[0] == 12 and ranks[1] >= 9:
            return True  # Q9+
        if ranks[0] == 11 and ranks[1] >= 9:
            return True  # J9+
        if is_suited and ranks[0] == 10 and ranks[1] >= 8:
            return True  # T8s+
        if is_suited and ranks[0] == 9 and ranks[1] >= 7:
            return True  # 97s+
        return False

    def declare_action(self, valid_actions, hole_card, round_state):
        self.socketio.emit('shift_player', {'name': self.name},room=self.room_id)
        print(f"--- {self.name} (National Champion) acting ---")
        eventlet.sleep(timeSleep())

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
        action_histories = round_state.get('action_histories', {})
        seats = round_state.get('seats', [])
        action_to_take = None
        amount = 0
        pot_size = _get_pot_size(round_state)
        active_players = _get_active_players_count(seats)

        # --- Nivel 8: Stack Awareness ---
        my_stack = _get_my_stack(seats, self.uuid)
        bb_amount = self.game_info.get('rule', {}).get('small_blind', 1) * 2
        if bb_amount == 0:
            bb_amount = 1
        my_stack_bb = my_stack / bb_amount
        print(f"{self.name} Stack: {my_stack} ({my_stack_bb:.1f} BB)")

        # --- Nivel 8: Lógica Push/Fold si corto de stack preflop ---
        PUSH_FOLD_THRESHOLD_BB = 15  # Umbral de BBs para push/fold
        if street == 'preflop' and my_stack_bb < PUSH_FOLD_THRESHOLD_BB:
            should_push = self._get_push_fold_range(my_hole_card)
            print(
                f"{self.name} Short stack ({my_stack_bb:.1f} BB). Push decision: {should_push} with {my_hole_card}")

            if should_push and raise_action:
                # Max raise es all-in
                all_in_amount = raise_action["amount"]["max"]
                # Asegurarse que el max_raise es al menos nuestro stack
                if all_in_amount >= my_stack:
                    amount = my_stack
                else:  # Si no, ir all-in con lo que podamos subir
                    amount = all_in_amount
                action_to_take = raise_action
                print(f"{self.name} Pushing All-in with {amount}")
                # Retornar directamente para push/fold
                self.socketio.emit(
                    "bot_action", {"player": self.name, "action": "raise", "amount": amount},room=self.room_id)
                return "raise", amount
            else:  # Foldear si no es mano de push o no podemos raisear
                action_to_take = fold_action if fold_action else check_action
                amount = 0
                print(f"{self.name} Folding short stack")
                # Default fold if no action
                action_str = action_to_take['action'] if action_to_take else 'fold'
                self.socketio.emit(
                    "bot_action", {"player": self.name, "action": action_str, "amount": amount},room=self.room_id)
                return action_str, amount

        # --- Lógica Normal (si no es push/fold) ---
        # (Similar a LocalLegend, con adición de bluff puro)
        is_premium_hand_preflop = self._is_premium_preflop(
            my_hole_card) if street == 'preflop' else False
        hand_strength = _evaluate_postflop_hand_stub(
            my_hole_card, community_card)
        has_draw = _has_strong_draw_stub(my_hole_card, community_card)
        is_value_hand = hand_strength in ["TWO_PAIR", "TRIPS_OR_BETTER"]
        is_decent_hand = hand_strength == "PAIR"

        # --- Nivel 8: Farol Puro Ocasional en River ---
        bluff_attempted = False
        pure_bluff_action = None
        if street == 'river' and not is_value_hand and not is_decent_hand and not has_draw and active_players == 2:
            # ¿Podemos apostar (somos primeros o checkearon antes)?
            can_bet = check_action is not None or any(
                h['action'] == 'CHECK' for h in action_histories.get('river', []))
            if can_bet and raise_action and random.random() < 0.15:  # 15% chance
                print(f"{self.name} Considering pure river bluff...")
                pure_bluff_action = raise_action  # Planear el bluff
                bluff_attempted = True

        # --- Lógica de Acción Principal (si no push/fold ni bluff puro planeado) ---
        if pure_bluff_action:
            action_to_take = pure_bluff_action
        elif street == 'preflop':  # Rehacer lógica preflop normal si no fue push/fold
            position = _get_my_position(round_state, self.uuid)
            preflop_history = action_histories.get('preflop', [])
            facing_raise = any(h['action'] == 'RAISE' and h.get(
                'player_uuid') != self.uuid for h in preflop_history)
            limpers = len([h for h in preflop_history if h['action']
                          == 'CALL' and h.get('paid', 0) == bb_amount])
            should_play = self._should_play_preflop_adjusted(
                my_hole_card, position, facing_raise, limpers)
            if should_play:
                raise_prob = 0.9 if is_premium_hand_preflop else (
                    0.5 if not facing_raise else 0.2)
                will_raise = raise_action and random.random() < raise_prob
                if will_raise:
                    action_to_take = raise_action
                    self.was_preflop_aggressor = True
                elif call_action:
                    action_to_take = call_action
                elif check_action:
                    action_to_take = check_action
                elif raise_action:
                    action_to_take = raise_action
                    self.was_preflop_aggressor = True
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
        # Lógica postflop normal (copiada/adaptada de LocalLegend)
        elif street != 'preflop':
            # C-Bet, check/call/raise/fold basado en hand_strength, draw, acción previa
            current_street_history = action_histories.get(street, [])
            street_aggression_level = sum(
                1 for h in current_street_history if h['action'] in ['RAISE'])
            aggression_modifier = 1.0
            if street_aggression_level >= 2:
                aggression_modifier = 0.5
            elif street_aggression_level == 1:
                aggression_modifier = 0.7
            if active_players > 2:
                aggression_modifier *= 0.8

            cbet_success = False
            if street == 'flop' and self.was_preflop_aggressor and check_action:
                cbet_prob = 0.65 * aggression_modifier
                if random.random() < cbet_prob:
                    action_to_take = raise_action
                    if action_to_take:
                        cbet_success = True

            if not cbet_success:
                if is_value_hand:
                    raise_prob = 0.80 * aggression_modifier
                    if raise_action and random.random() < raise_prob:
                        action_to_take = raise_action
                    elif call_action:
                        action_to_take = call_action
                    elif check_action:
                        action_to_take = check_action
                    else:
                        action_to_take = raise_action if raise_action else fold_action
                elif is_decent_hand:
                    # (Lógica similar a LocalLegend para jugar pares)
                    fold_prob = 0.3 if street_aggression_level >= 1 and active_players > 1 else 0.0
                    if fold_action and random.random() < fold_prob:
                        action_to_take = fold_action
                    else:
                        raise_prob = 0.10 * aggression_modifier
                        if raise_action and random.random() < raise_prob:
                            action_to_take = raise_action
                        elif call_action:
                            action_to_take = call_action
                        elif check_action:
                            action_to_take = check_action
                        else:
                            action_to_take = fold_action if fold_action else random.choice(
                                valid_actions)
                elif has_draw:
                    # (Lógica similar a LocalLegend para jugar draws)
                    semi_bluff_chance = 0.30 * aggression_modifier
                    if raise_action and random.random() < semi_bluff_chance:
                        action_to_take = raise_action
                    elif call_action:
                        call_amount = call_action['amount']
                        effective_pot = pot_size + call_amount
                        pot_odds = call_amount / effective_pot if effective_pot > 0 else 1
                        reasonable_odds = pot_odds < (
                            0.35 if active_players <= 2 else 0.25)
                        if reasonable_odds:
                            action_to_take = call_action
                        elif fold_action:
                            action_to_take = fold_action
                        else:
                            action_to_take = call_action
                    elif check_action:
                        action_to_take = check_action
                    else:
                        action_to_take = fold_action if fold_action else random.choice(
                            valid_actions)
                else:  # HIGH_CARD
                    # (Lógica similar a LocalLegend para foldear/checkear)
                    fold_prob = 0.4 * \
                        (1 + street_aggression_level) if call_action else 0.0
                    if fold_action and random.random() < fold_prob:
                        action_to_take = fold_action
                    elif check_action:
                        action_to_take = check_action
                    elif fold_action:
                        action_to_take = fold_action
                    else:
                        action_to_take = call_action if call_action else random.choice(
                            valid_actions)

        # Fallback final
        if not action_to_take:
            action_to_take = check_action if check_action else call_action if call_action else fold_action if fold_action else raise_action if raise_action else random.choice(
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
                    # Determinar tipo de raise para sizing
                    is_value_raise = (street != 'preflop' and is_value_hand) or \
                                     (street == 'preflop' and is_premium_hand_preflop)
                    is_pure_bluff = bluff_attempted
                    is_semi_bluff = False  # Podríamos refinar esto
                    is_cbet = False  # Podríamos refinar esto

                    target_bet_fraction = 0.6  # Default
                    if is_pure_bluff:
                        target_bet_fraction = random.uniform(0.50, 0.70)
                    elif is_value_raise:
                        target_bet_fraction = random.uniform(0.60, 0.85)
                    # ... (añadir sizing para cbet, semi_bluff si se trackea mejor) ...
                    else:
                        target_bet_fraction = random.uniform(0.50, 0.70)

                    target_bet_size = pot_size * target_bet_fraction
                    to_call = call_action['amount'] if call_action else 0
                    total_raise_amount = to_call + target_bet_size
                    amount = int(
                        max(min_raise, min(max_raise, total_raise_amount)))

                    if amount < min_raise:
                        amount = min_raise
                    if amount <= 0 and min_raise > 0:
                        amount = min_raise
                    print(f"{self.name} {'PureBluff' if is_pure_bluff else 'Value' if is_value_raise else 'Standard'} Raise - Target bet: {target_bet_fraction*100:.0f}% pot -> Amount: {amount}")

            elif action_type == "call":
                amount = action_to_take["amount"]
            else:
                amount = 0
        else:
            print(f"ERROR: {self.name} no pudo decidir una acción.")
            return "fold", 0

        # Clamp final
        if action_to_take['action'] == 'raise':
            min_r, max_r = action_to_take['amount']['min'], action_to_take['amount']['max']
            
            if min_r != -1:
                amount = max(min_r, min(amount, max_r))

        print(
            f"{self.name} chooses: {action_to_take['action']} {amount if amount > 0 else ''}")
        self.socketio.emit("bot_action", {
                           "player": self.name, "action": action_to_take["action"], "amount": amount},room=self.room_id)
        return action_to_take["action"], amount

    # ... (receive_* messages iguales que LocalLegend) ...
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
        self.was_preflop_aggressor = False
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

