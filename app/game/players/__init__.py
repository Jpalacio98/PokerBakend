# app/game/players/__init__.py
import random
from pypokerengine.utils.card_utils import gen_cards # Necesario para el stub

# --- Función de Tiempo de Espera ---
def timeSleep():
    """Genera un tiempo de espera aleatorio."""
    # Puedes ajustar estos valores según prefieras
    return random.choice([random.uniform(0.8, 2.5) for _ in range(6)])

# --- Funciones Auxiliares de Juego ---

def _get_pot_size(round_state):
    """Calcula el tamaño total del bote principal actual."""
    return round_state.get('pot', {}).get('main', {}).get('amount', 0)

def _get_active_players_count(seats):
    """Cuenta cuántos jugadores siguen en la mano (no 'folded')."""
    return sum(1 for player in seats if player.get('state') != 'folded')

def _get_my_stack(seats, my_uuid):
    """Obtiene el stack del jugador actual."""
    for player in seats:
        if player.get('uuid') == my_uuid:
            return player.get('stack', 0)
    return 0

def _card_rank_to_int(rank_str):
    """Convierte rank T, J, Q, K, A a número."""
    if rank_str is None: return 0 # Seguridad
    if rank_str.isdigit():
        return int(rank_str)
    else:
        return {'T': 10, 'J': 11, 'Q': 12, 'K': 13, 'A': 14}.get(rank_str, 0)

def _get_my_position(round_state, my_uuid):
    """Determina la posición relativa (simplificado)."""
    seats = round_state.get('seats', [])
    dealer_btn_pos = round_state.get('dealer_btn', 0)
    num_players = len(seats)
    my_pos_abs = -1
    for i, player in enumerate(seats):
        if player.get('uuid') == my_uuid:
            my_pos_abs = i
            break
    if my_pos_abs == -1 or num_players == 0: return "unknown"

    relative_pos = (my_pos_abs - dealer_btn_pos - 1 + num_players) % num_players
    if num_players <= 3: return "late" if relative_pos == num_players - 1 else "early"
    elif num_players <= 6:
        if relative_pos <= 1: return "early"
        elif relative_pos <= 3 : return "middle"
        else: return "late"
    else:
        if relative_pos <= 2: return "early"
        elif relative_pos <= 5: return "middle"
        else: return "late"

# --- STUB: Funciones de Evaluación (¡Necesitas Implementaciones Reales!) ---

def _is_strong_preflop_simple(hole_card):
    """Placeholder MUY básico para evaluar manos preflop."""
    if not hole_card or len(hole_card) < 2: return False
    ranks = sorted([_card_rank_to_int(c[1]) for c in hole_card], reverse=True)
    suits = [c[0] for c in hole_card]
    is_suited = suits[0] == suits[1]
    is_pair = ranks[0] == ranks[1]

    if is_pair and ranks[0] >= 9: return True # 99+
    if ranks[0] == 14 and ranks[1] >= 11: return True # AQ+, AK
    if ranks[0] == 13 and ranks[1] >= 12: return True # KQ
    if is_suited and ranks[0] == 14 and ranks[1] >= 10: return True # ATs+
    if is_suited and ranks[0] == 13 and ranks[1] >= 10: return True # KTs+
    if is_suited and ranks[0] == 12 and ranks[1] >= 10: return True # QTs+
    if not is_suited and ranks[0] <= 8 and ranks[1] <= 5: return False # 85o o peor
    return True # Jugar muchas otras manos (podría refinarse)

def _evaluate_postflop_hand_stub(hole_card, community_card):
    """
    ¡¡¡PLACEHOLDER IMPORTANTE!!! Necesitas reemplazar esto con una librería real.
    Devuelve: "TRIPS_OR_BETTER", "TWO_PAIR", "PAIR", "HIGH_CARD".
    """
    if not community_card or len(community_card) < 3: return "HIGH_CARD"
    # Lógica de ejemplo extremadamente simplificada (¡NO USAR EN PRODUCCIÓN!)
    all_cards_str = hole_card + community_card
    ranks = [_card_rank_to_int(c[1]) for c in all_cards_str]
    rank_counts = {r: ranks.count(r) for r in set(ranks)}
    pairs = sum(1 for count in rank_counts.values() if count == 2)
    trips = sum(1 for count in rank_counts.values() if count == 3)
    quads = sum(1 for count in rank_counts.values() if count == 4)
    uses_hole_card = False # Simplificación: Asumir que sí si tenemos par o mejor
    hole_ranks = [_card_rank_to_int(c[1]) for c in hole_card]
    for hr in hole_ranks:
        if rank_counts.get(hr, 0) >= 2: uses_hole_card = True; break
    if not uses_hole_card and len(hole_card) > 0:
         board_ranks = [_card_rank_to_int(c[1]) for c in community_card]
         board_rank_counts = {r: board_ranks.count(r) for r in set(board_ranks)}
         board_pairs = sum(1 for count in board_rank_counts.values() if count == 2)
         if pairs > board_pairs : uses_hole_card = True

    if not uses_hole_card and pairs > 0 : return "HIGH_CARD" # Solo par en mesa

    if quads >= 1: return "TRIPS_OR_BETTER"
    if trips >= 1 and pairs >= 1: return "TRIPS_OR_BETTER"
    if trips >= 1: return "TRIPS_OR_BETTER"
    if pairs >= 2: return "TWO_PAIR"
    if pairs == 1: return "PAIR"
    return "HIGH_CARD"

def _has_strong_draw_stub(hole_card, community_card):
    """¡PLACEHOLDER! Detecta proyectos fuertes (color o escalera abierta)."""
    if not community_card or len(community_card) < 3 or len(community_card) > 4: return False
    all_cards_str = hole_card + community_card
    suits = [c[0] for c in all_cards_str]
    ranks = sorted(list(set(_card_rank_to_int(c[1]) for c in all_cards_str)), reverse=True)
    suit_counts = {s: suits.count(s) for s in set(suits)}
    if any(count == 4 for count in suit_counts.values()):
        flush_suit = next(s for s, count in suit_counts.items() if count == 4)
        if any(c[0] == flush_suit for c in hole_card): return True
    for i in range(len(ranks) - 3):
        is_oesd = all(ranks[i+j] == ranks[i] - j for j in range(4))
        if is_oesd:
            draw_ranks = set(ranks[i:i+4])
            hole_ranks_set = set(_card_rank_to_int(c[1]) for c in hole_card)
            if any(hr in draw_ranks for hr in hole_ranks_set):
                 board_ranks_set = set(_card_rank_to_int(c[1]) for c in community_card)
                 if not draw_ranks.issubset(board_ranks_set): return True
    return False

# Para que se puedan importar más fácilmente (opcional)
__all__ = [
    'timeSleep', '_get_pot_size', '_get_active_players_count', '_get_my_stack',
    '_card_rank_to_int', '_get_my_position', '_is_strong_preflop_simple',
    '_evaluate_postflop_hand_stub', '_has_strong_draw_stub'
]