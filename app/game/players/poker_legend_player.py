# app/game/players/poker_legend_player.py
import random
import eventlet
from pypokerengine.players import BasePokerPlayer
# Importar funciones desde __init__.py
from . import (timeSleep, _get_my_position, _card_rank_to_int,
               _evaluate_postflop_hand_stub, _has_strong_draw_stub,
               _get_pot_size, _get_active_players_count, _get_my_stack)  # Asegúrate que _get_my_stack está importado


class PokerLegendPlayer(BasePokerPlayer):
    def __init__(self, socketio, name, image,room_id):
        self.name = name
        self.image = image
        self.socketio = socketio
        self.uuid = None
        self.hole_card = []
        self.game_info = {}
        self.was_preflop_aggressor = False
        self.opponent_stats = {}
        self.recent_aggression_score = 0
        self.room_id=room_id

    # --- Helpers ---
    def _is_premium_preflop(self, hole_card):  # Copiar de GPM
        if not hole_card or len(hole_card) < 2:
            return False
        ranks = sorted([_card_rank_to_int(c[1])
                       for c in hole_card], reverse=True)
        is_pair = ranks[0] == ranks[1]
        return (is_pair and ranks[0] >= 12) or (ranks[0] == 14 and ranks[1] == 13)

    def _is_speculative_preflop(self, hole_card):  # Copiar de GPM
        if not hole_card or len(hole_card) < 2:
            return False
        ranks = sorted([_card_rank_to_int(c[1])
                       for c in hole_card], reverse=True)
        is_suited = hole_card[0][0] == hole_card[1][0]
        is_connected = abs(ranks[0]-ranks[1]) <= 2
        is_pair = ranks[0] == ranks[1]
        return (is_suited and is_connected and ranks[0] < 11) or (is_pair and ranks[0] < 7)

    # Copiar de GPM
    def _should_play_preflop_adjusted(self, hole_card, position, facing_raise, limpers):
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

    def _should_play_preflop_base(self, hole_card, position):  # Copiar de GPM
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
            if is_suited and abs(ranks[0]-ranks[1]) == 1 and ranks[0] >= 8:
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
            if is_suited and abs(ranks[0]-ranks[1]) == 1 and ranks[0] >= 6:
                return True
            if not is_suited and ranks[0] >= 12 and ranks[1] >= 10:
                return True
        return False

    def _get_push_fold_range(self, hole_card):  # Copiar de GPM
        if not hole_card or len(hole_card) < 2:
            return False
        ranks = sorted([_card_rank_to_int(c[1])
                       for c in hole_card], reverse=True)
        is_pair = ranks[0] == ranks[1]
        is_suited = hole_card[0][0] == hole_card[1][0]
        if is_pair and ranks[0] >= 5:
            return True
        if ranks[0] == 14 and ranks[1] >= 2:
            return True
        if ranks[0] == 13 and ranks[1] >= 7:
            return True
        if ranks[0] == 12 and ranks[1] >= 9:
            return True
        if ranks[0] == 11 and ranks[1] >= 9:
            return True
        if is_suited and ranks[0] == 10 and ranks[1] >= 8:
            return True
        if is_suited and ranks[0] == 9 and ranks[1] >= 7:
            return True
        return False
    # --- Fin Helpers ---

    def declare_action(self, valid_actions, hole_card, round_state):
        self.socketio.emit('shift_player', {'name': self.name},room=self.room_id)
        print(f"--- {self.name} (Poker Legend) acting ---")
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

        # FIX: Calcular my_stack y my_stack_bb ANTES de usarlos en push/fold
        my_stack = _get_my_stack(seats, self.uuid)
        bb_amount = self.game_info.get('rule', {}).get('small_blind', 1) * 2
        if bb_amount == 0:
            bb_amount = 1
        my_stack_bb = my_stack / bb_amount
        print(f"{self.name} Stack: {my_stack} ({my_stack_bb:.1f} BB)")

        # FIX: Variable para premium preflop
        is_premium_hand_preflop_calc = False

        # --- Lógica Push/Fold ---
        PUSH_FOLD_THRESHOLD_BB = 15
        if street == 'preflop' and my_stack_bb < PUSH_FOLD_THRESHOLD_BB:
            # ... (Copiar lógica Push/Fold de GPM y retornar si aplica) ...
            should_push = self._get_push_fold_range(my_hole_card)
            if should_push and raise_action:
                # FIX: Usar my_stack (ya calculado) y lógica correcta de all-in
                all_in_raise_amount = raise_action["amount"]["max"]
                if all_in_raise_amount >= my_stack:
                    amount = my_stack
                else:
                    amount = all_in_raise_amount
                action_to_take = raise_action
                print(f"{self.name} Pushing All-in with {amount}")
                self.socketio.emit(
                    "bot_action", {"player": self.name, "action": "raise", "amount": amount},room=self.room_id)
                return "raise", amount
            else:
                action_to_take = fold_action if fold_action else check_action
                action_str = action_to_take['action'] if action_to_take else 'fold'
                print(f"{self.name} Folding short stack")
                self.socketio.emit(
                    "bot_action", {"player": self.name, "action": action_str, "amount": 0},room=self.room_id)
                return action_str, 0

        # --- Nivel 10: Modificadores (Exploit, Blockers, Meta) ---
        # ... (Código de modificadores igual que antes) ...
        exploit_modifier_cbet = 1.0
        exploit_modifier_bluff_catch = 1.0
        opponent_aggression = 1.0
        if active_players == 2:
            opponent_uuid = next(
                (p['uuid'] for p in seats if p['uuid'] != self.uuid and p['state'] != 'folded'), None)
            if opponent_uuid:
                stats = self.opponent_stats.get(
                    opponent_uuid, {"fold_to_cbet": 0.5, "agg_factor": 1.0})
                fold_rate = stats["fold_to_cbet"]
                opponent_aggression = stats["agg_factor"]
                print(
                    f"{self.name} Opponent {opponent_uuid[:4]} F@CB(sim):{fold_rate:.2f}, Agg(sim):{opponent_aggression:.1f}")
                if fold_rate > 0.65:
                    exploit_modifier_cbet = 1.4
                elif fold_rate < 0.4:
                    exploit_modifier_cbet = 0.6
                if opponent_aggression > 2.0:
                    exploit_modifier_bluff_catch = 0.7
                elif opponent_aggression < 0.8:
                    exploit_modifier_bluff_catch = 1.3

        blocker_effect_modifier = 1.0
        if street == 'river':
            suits_on_board = [c[0] for c in community_card]
            flush_suit = next(
                (s for s in "SHDC" if suits_on_board.count(s) >= 3), None)
            if flush_suit and any(card == flush_suit + 'A' for card in my_hole_card):
                print(
                    f"{self.name} Blocker: Holding Nut Flush blocker ({flush_suit}A)")
                blocker_effect_modifier = 1.1

        meta_game_modifier = 1.0
        if self.recent_aggression_score > 3:
            meta_game_modifier = 0.8
            print(
                f"{self.name} Meta: High aggro ({self.recent_aggression_score:.1f}) -> Passive lean")
        elif self.recent_aggression_score < -3:
            meta_game_modifier = 1.2
            print(
                f"{self.name} Meta: Low aggro ({self.recent_aggression_score:.1f}) -> Aggro lean")

        # --- Lógica Normal ---
        hand_strength = _evaluate_postflop_hand_stub(
            my_hole_card, community_card)
        has_draw = _has_strong_draw_stub(my_hole_card, community_card)
        is_monster_hand = hand_strength == "TRIPS_OR_BETTER"
        is_value_hand = is_monster_hand or hand_strength == "TWO_PAIR"
        is_decent_hand = hand_strength == "PAIR"
        is_strong_draw = has_draw

        planning_check_raise_check = False
        # ... (lógica check/raise planning) ...

        balanced_action = None  # Slow Play
        if not planning_check_raise_check and is_monster_hand and random.random() < 0.15 * meta_game_modifier:
            if check_action:
                balanced_action = check_action
                print(f"{self.name} Balance: Slow playing monster with check.")
            elif call_action:
                balanced_action = call_action
                print(f"{self.name} Balance: Slow playing monster with call.")

        # --- Lógica de Acción Principal (si no push/fold, ni check/raise plan, ni slow play) ---
        if not planning_check_raise_check and balanced_action is None:
            if street == 'preflop':
                # ... (lógica preflop como GPM, usando meta_game_modifier y guardando is_premium_hand_preflop_calc) ...
                position = _get_my_position(round_state, self.uuid)
                preflop_history = action_histories.get('preflop', [])
                facing_raise = any(h['action'] == 'RAISE' and h.get(
                    'player_uuid') != self.uuid for h in preflop_history)
                limpers = len([h for h in preflop_history if h['action']
                              == 'CALL' and h.get('paid', 0) == bb_amount])
                should_play = self._should_play_preflop_adjusted(
                    my_hole_card, position, facing_raise, limpers)
                is_premium_hand_preflop_calc = self._is_premium_preflop(
                    my_hole_card)  # Guardar valor
                if should_play:
                    raise_prob = 0.9 if is_premium_hand_preflop_calc else (
                        0.55 if not facing_raise else 0.25)
                    raise_prob *= meta_game_modifier  # Ajustar por meta
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

            else:  # Lógica Postflop (adaptada de GPM con balance/meta/blocker)
                # ... (código postflop como GPM, pero ajustar probabilidades con todos los modificadores) ...
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
                    cbet_prob = 0.70 * exploit_modifier_cbet * \
                        aggression_modifier * meta_game_modifier
                    if random.random() < cbet_prob:
                        action_to_take = raise_action
                        if action_to_take:
                            cbet_success = True

                if not cbet_success:
                    if is_value_hand:  # Jugar valor (no slow played)
                        raise_prob = 0.85 * aggression_modifier * meta_game_modifier
                        if raise_action and random.random() < raise_prob:
                            action_to_take = raise_action
                        elif call_action:
                            action_to_take = call_action
                        elif check_action:
                            action_to_take = check_action
                        else:
                            action_to_take = raise_action if raise_action else fold_action
                    elif is_decent_hand:  # Jugar par
                        call_prob_mod = exploit_modifier_bluff_catch * meta_game_modifier
                        fold_prob = 0.2 if street_aggression_level >= 1 else 0.0
                        if fold_action and random.random() < fold_prob:
                            action_to_take = fold_action
                        else:
                            raise_prob = 0.10 * aggression_modifier * meta_game_modifier
                            if raise_action and random.random() < raise_prob:
                                action_to_take = raise_action
                            elif call_action and random.random() < call_prob_mod:
                                action_to_take = call_action
                            elif check_action:
                                action_to_take = check_action
                            elif call_action:
                                action_to_take = call_action
                            else:
                                action_to_take = fold_action if fold_action else random.choice(
                                    valid_actions)
                    elif has_draw:  # Jugar proyecto
                        semi_bluff_chance = 0.35 * exploit_modifier_cbet * \
                            aggression_modifier * meta_game_modifier
                        if raise_action and random.random() < semi_bluff_chance:
                            action_to_take = raise_action
                        elif call_action:  # Odds check
                            call_amount = call_action['amount']
                            effective_pot = pot_size+call_amount
                            pot_odds = call_amount/effective_pot if effective_pot > 0 else 1
                            reasonable_odds = pot_odds < 0.40
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
                        pure_bluff_river = False
                        if street == 'river' and active_players == 2 and check_action and raise_action:
                            bluff_prob = 0.12 * exploit_modifier_cbet * \
                                blocker_effect_modifier * meta_game_modifier
                            if random.random() < bluff_prob:
                                action_to_take = raise_action
                                pure_bluff_river = True
                                print(
                                    f"{self.name} Attempting Pure River Bluff")
                        if not pure_bluff_river:
                            if check_action:
                                action_to_take = check_action
                            elif fold_action:
                                action_to_take = fold_action
                            else:
                                action_to_take = call_action if call_action else random.choice(
                                    valid_actions)

        elif balanced_action:  # Si decidimos slowplay/trap
            action_to_take = balanced_action

        # Fallback final
        if not action_to_take:
            action_to_take = check_action if check_action else call_action if call_action else fold_action if fold_action else raise_action if raise_action else random.choice(
                valid_actions)

        # --- Calcular Amount (con varianza para balance) ---
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
                    # FIX: Usar is_premium_hand_preflop_calc
                    is_value_raise = (street != 'preflop' and is_value_hand) or \
                                     (street == 'preflop' and is_premium_hand_preflop_calc)
                    is_pure_bluff = (
                        street == 'river' and not is_value_hand and not is_decent_hand and not has_draw and action_type == 'raise')

                    base_fraction = 0.65
                    if is_pure_bluff:
                        base_fraction = random.uniform(0.55, 0.80)
                    elif is_value_raise:
                        base_fraction = random.uniform(0.60, 0.90)
                    else:
                        base_fraction = random.uniform(0.55, 0.75)

                    variance = random.uniform(-0.1, 0.1)  # Añadir varianza
                    target_bet_fraction = max(
                        0.3, min(1.0, base_fraction + variance))

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

        # --- Actualizar Meta-juego Score ---
        if action_to_take['action'] in ['raise']:
            self.recent_aggression_score += 1
        elif action_to_take['action'] in ['call', 'check']:
            self.recent_aggression_score -= 0.5
        self.recent_aggression_score = max(-5,
                                           min(5, self.recent_aggression_score * 0.99))

        # Clamp final
        if action_to_take['action'] == 'raise':
            min_r, max_r = action_to_take['amount']['min'], action_to_take['amount']['max']
            if min_r != -1:
                amount = max(min_r, min(amount, max_r))

        print(
            f"{self.name} chooses: {action_to_take['action']} {amount if amount > 0 else ''} (AggroScore: {self.recent_aggression_score:.1f})")
        self.socketio.emit("bot_action", {
                           "player": self.name, "action": action_to_take["action"], "amount": amount},room=self.room_id)
        return action_to_take["action"], amount

    # ... (receive_* messages iguales que GrandMaster) ...
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
    # Placeholder para actualizar stats/meta
    def receive_game_update_message(self, action, round_state):
        self.socketio.emit(
            "game_update", {"action": action, "round_state": round_state},room=self.room_id)

    def receive_round_result_message(
            self, winners, hand_info, round_state):
        win = any(self.name == win['name'] for win in winners)
        if win:
            self.socketio.emit(
                "winners", {"winners": winners}, room=self.room_id)
