from pypokerengine.engine.card import Card
from app.game.hand_evaluator import HandEvaluator
players_hand =[]


def eval_had(hole,community):
    HandEvaluator
    if len(hole) == 0:
        return "None"
    else:
        hole_cards= []
        for item in hole:
            c = Card.from_str(item)

            hole_cards.append(c)
        community_cards= []
        for item in community:
            c = Card.from_str(item)
            community_cards.append(c)
        hand = HandEvaluator().eval_hand(hole_cards,community_cards)
        row_strength = HandEvaluator().mask_hand_strength(hand)
        strength = HandEvaluator().HAND_STRENGTH_MAP[row_strength]
        return {'strength':strength , 'row_strength':row_strength,'hand_value':hand }

def get_weight(strength):
    """
    Asigna un valor de peso a una mano de póker basado en su strength.

    Parámetros:
    strength (str): El strength de la mano (e.g., "HIGHCARD", "ONEPAIR", etc.).

    Retorna:
    int: Un valor numérico que representa el peso de la mano.
    """
    strength_weight_map = {
        "HIGHCARD": 1,
        "ONEPAIR": 2,
        "TWOPAIR": 3,
        "THREECARD": 4,
        "STRAIGHT": 5,
        "FLUSH": 6,
        "FULLHOUSE": 7,
        "FOURCARD": 8,
        "STRAIGHTFLUSH": 9
    }

    return strength_weight_map.get(strength, 0)

