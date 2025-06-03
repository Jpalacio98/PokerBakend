# app/game/players/local_legend_player.py
import random
import eventlet
from pypokerengine.players import BasePokerPlayer
# Importar funciones desde __init__.py
from . import (timeSleep, _get_my_position, _card_rank_to_int,
               _evaluate_postflop_hand_stub, _has_strong_draw_stub,
               _get_pot_size, _get_active_players_count, _is_strong_preflop_simple)


class LocalLegendPlayer(BasePokerPlayer):
    def __init__(self, socketio, name, image,room_id):
        self.name = name
        self.image = image
        self.socketio = socketio
        self.uuid = None
        self.hole_card = []
        self.game_info = {}
        self.was_preflop_aggressor = False
        self.room_id=room_id

    # Helpers internos (podrían estar en __init__ si son más complejos)
    def _is_premium_preflop(self, hole_card):
        if not hole_card or len(hole_card) < 2:
            return False
        ranks = sorted([_card_rank_to_int(c[1])
                       for c in hole_card], reverse=True)
        is_pair = ranks[0] == ranks[1]
        # QQ+, AK
        return (is_pair and ranks[0] >= 12) or (ranks[0] == 14 and ranks[1] == 13)

    def _is_speculative_preflop(self, hole_card):
        if not hole_card or len(hole_card) < 2:
            return False
        ranks = sorted([_card_rank_to_int(c[1])
                       for c in hole_card], reverse=True)
        is_suited = hole_card[0][0] == hole_card[1][0]
        is_connected = abs(ranks[0] - ranks[1]) <= 2  # Conectadas o 1-gapper
        is_pair = ranks[0] == ranks[1]
        # Suited connectors bajos, pares bajos
        return (is_suited and is_connected and ranks[0] < 11) or (is_pair and ranks[0] < 7)

    def _should_play_preflop_adjusted(self, hole_card, position, facing_raise, limpers):
        """Ajusta el rango preflop basado en la acción."""
        base_play = self._should_play_preflop_base(
            hole_card, position)  # Usa la lógica base

        if facing_raise:
            # Jugar mucho más tight contra un raise
            if self._is_premium_preflop(hole_card):
                return True  # Siempre jugar premium
            # Jugar manos fuertes como AK, AQs, JJ, TT con cierta probabilidad
            if (_card_rank_to_int(hole_card[0][1]) == 14 and _card_rank_to_int(hole_card[1][1]) >= 12) or \
               (_card_rank_to_int(hole_card[0][1]) >= 10 and _card_rank_to_int(hole_card[1][1]) >= 10 and hole_card[0][1] == hole_card[1][1]):  # TT+
                return random.random() < 0.7  # Chance de jugar estas
            return False  # Foldear el resto
        elif limpers >= 2:
            # Jugar un poco más loose con limpers (buscar flops multiway)
            if base_play:
                return True
            # Añadir especulativas
            if self._is_speculative_preflop(hole_card) and random.random() < 0.4:
                return True
            return False
        else:
            # Sin acción fuerte, usar el rango base
            return base_play

    def _should_play_preflop_base(self, hole_card, position):
        """Define rangos base por posición (igual que Shark/Expert)."""
        if not hole_card or len(hole_card) < 2:
            return False
        ranks = sorted([_card_rank_to_int(c[1])
                       for c in hole_card], reverse=True)
        is_pair = ranks[0] == ranks[1]
        is_suited = hole_card[0][0] == hole_card[1][0]
        # (Lógica de rangos base)
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

    def declare_action(self, valid_actions, hole_card, round_state):
        self.socketio.emit('shift_player', {'name': self.name},room=self.room_id)
        print(f"--- {self.name} (Local Legend) acting ---")
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
        action_histories = round_state.get('action_histories', {})  # Historial
        seats = round_state.get('seats', [])
        action_to_take = None
        amount = 0
        pot_size = _get_pot_size(round_state)
        active_players = _get_active_players_count(seats)

        is_premium_hand_preflop = False
        cbet_attempted = False 
        
        if street == 'preflop':
            position = _get_my_position(round_state, self.uuid)
            # --- Nivel 7: Adaptación Preflop ---
            preflop_history = action_histories.get('preflop', [])
            raises_before_me = [h for h in preflop_history if h['action']
                                == 'RAISE' and h.get('player_uuid') != self.uuid]
            facing_raise = bool(raises_before_me)
            limpers = len([h for h in preflop_history if h['action'] == 'CALL' and h.get(
                'paid', 0) == self.game_info.get('rule', {}).get('small_blind', 1) * 2])

            print(
                f"{self.name} Pos: {position}, Facing Raise: {facing_raise}, Limpers: {limpers}")
            should_play = self._should_play_preflop_adjusted(
                my_hole_card, position, facing_raise, limpers)
            is_premium_hand_preflop = self._is_premium_preflop(my_hole_card)

            if should_play:
                # Raise más probable con premium o si no hay raise previo
                raise_prob = 0.0
                if is_premium_hand_preflop:
                    raise_prob = 0.9  # Casi siempre raise premium
                elif not facing_raise:
                    raise_prob = 0.5  # Raise 50% si abrimos nosotros
                else:
                    raise_prob = 0.2  # Raise (3bet) menos probable vs raise

                will_raise = raise_action and random.random() < raise_prob

                if will_raise:
                    action_to_take = raise_action
                    self.was_preflop_aggressor = True
                elif call_action:
                    action_to_take = call_action
                elif check_action:
                    action_to_take = check_action
                elif raise_action:  # Fallback raise
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

        else:  # Flop, Turn, River
            hand_strength = _evaluate_postflop_hand_stub(
                my_hole_card, community_card)
            has_draw = _has_strong_draw_stub(my_hole_card, community_card)
            print(
                f"{self.name} Postflop Hand: {hand_strength}, Draw: {has_draw}, Pot: {pot_size}, Active: {active_players}")

            # --- Nivel 7: Adaptación Postflop ---
            current_street_history = action_histories.get(street, [])
            street_has_raise = any(
                h['action'] == 'RAISE' for h in current_street_history)
            # ¿Cuántas apuestas/subidas hubo en esta calle?
            street_aggression_level = sum(
                1 for h in current_street_history if h['action'] in ['RAISE'])

            is_value_hand = hand_strength in ["TWO_PAIR", "TRIPS_OR_BETTER"]
            is_decent_hand = hand_strength == "PAIR"

            # Modificador de agresividad base
            aggression_modifier = 1.0
            if street_aggression_level >= 2:
                aggression_modifier = 0.5  # Muy cauto vs 3bet+
            elif street_has_raise:
                aggression_modifier = 0.7
            if active_players > 2:
                aggression_modifier *= 0.8  # Cautela multiway

            # C-Bet (similar a Shark, quizás ajustar probabilidad)
            cbet_attempted = False
            if street == 'flop' and self.was_preflop_aggressor and check_action:
                # Cbet menos probable multiway o vs agresión
                cbet_prob = 0.65 * aggression_modifier
                if random.random() < cbet_prob:
                    action_to_take = raise_action
                    if action_to_take:
                        cbet_attempted = True

            # --- Lógica de Acción (si no C-Bet) ---
            if not cbet_attempted:
                if is_value_hand:
                    raise_prob = 0.80 * aggression_modifier  # Menos raise vs agresión
                    if raise_action and random.random() < raise_prob:
                        action_to_take = raise_action
                    elif call_action:
                        action_to_take = call_action
                    elif check_action:
                        action_to_take = check_action
                    else:
                        action_to_take = raise_action if raise_action else fold_action
                elif is_decent_hand:
                    # Foldear par medio/bajo vs mucha agresión o multiway
                    fold_prob = 0.0
                    if street_aggression_level >= 1 and active_players > 1:
                        fold_prob = 0.3
                    # Par bajo
                    if hand_strength == "PAIR" and _card_rank_to_int(my_hole_card[0][1]) < 10:
                        fold_prob = max(
                            fold_prob, 0.2 if street_aggression_level >= 1 else 0.0)

                    if fold_action and random.random() < fold_prob:
                        action_to_take = fold_action
                        print(
                            f"{self.name} Folding decent hand due to action/players")
                    else:
                        raise_prob = 0.10 * aggression_modifier  # Raise raro
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
                    semi_bluff_chance = 0.30 * aggression_modifier  # Menos semi-bluff vs agresión
                    if raise_action and random.random() < semi_bluff_chance:
                        action_to_take = raise_action
                    elif call_action:  # Considerar odds
                        call_amount = call_action['amount']
                        effective_pot = pot_size + call_amount
                        pot_odds = call_amount / effective_pot if effective_pot > 0 else 1
                        reasonable_odds = pot_odds < (
                            0.35 if active_players <= 2 else 0.25)  # Peores odds multiway
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
                    # Foldear más rápido vs agresión
                    fold_prob = 0.0
                    if call_action:
                        # Más probable fold vs bet/raise
                        fold_prob = 0.4 * (1 + street_aggression_level)
                    if fold_action and random.random() < fold_prob:
                        action_to_take = fold_action
                    elif check_action:
                        action_to_take = check_action
                    elif fold_action:
                        action_to_take = fold_action  # Si no check, fold vs bet
                    else:
                        action_to_take = call_action if call_action else random.choice(
                            valid_actions)  # Raro

        # Fallback
        if not action_to_take:
            action_to_take = check_action if check_action else call_action if call_action else fold_action if fold_action else raise_action if raise_action else random.choice(
                valid_actions)

        # --- Calcular Amount (similar a Shark/Expert, usando pot size) ---
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
                    is_semi_bluff = (
                        street != 'preflop' and has_draw and not is_value_hand and not is_decent_hand and action_type == 'raise')
                    is_cbet = cbet_attempted

                    target_bet_fraction = 0.55  # Default un poco más grande
                    if is_cbet:
                        target_bet_fraction = random.uniform(0.33, 0.55)
                    elif is_value_raise:
                        target_bet_fraction = random.uniform(0.55, 0.85)
                    elif is_semi_bluff:
                        target_bet_fraction = random.uniform(0.50, 0.75)
                    else:
                        target_bet_fraction = random.uniform(0.45, 0.65)

                    # Ajustar tamaño por agresión? (Opcional, puede ser contraproducente)
                    # target_bet_fraction *= aggression_modifier

                    target_bet_size = pot_size * target_bet_fraction
                    to_call = call_action['amount'] if call_action else 0
                    total_raise_amount = to_call + target_bet_size
                    amount = int(
                        max(min_raise, min(max_raise, total_raise_amount)))

                    if amount < min_raise:
                        amount = min_raise
                    if amount <= 0 and min_raise > 0:
                        amount = min_raise
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

    # ... (receive_* messages iguales que Shark) ...
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

