# human_player.py
import eventlet  # Importar si usas eventlet en otros lugares, aunque no directamente aquí
from threading import Event
from pypokerengine.players import BasePokerPlayer
# Quitar imports no usados directamente en esta clase si no los necesitas aquí
# from app.game import players_hand, eval_had


class HumanPlayer(BasePokerPlayer):
    def __init__(self, socketio, name, image, room_id):
        self.name = name
        self.image = image
        self.socketio = socketio
        self.action_event = Event()
        self.current_action = None
        self.hole_card = []
        self.room_id = room_id


    def declare_action(self, valid_actions, hole_card, round_state):
        """
        Solicita una acción al jugador humano y la valida antes de devolverla.
        """
        print(f"--- Waiting for Human action: {self.name} ---")
        self.hole_card = hole_card  # Actualizar cartas por si acaso

        while True:  # Bucle hasta recibir una acción válida
            self.current_action_data = None  # Resetear acción previa
            self.action_event.clear()  # Asegurarse que está listo para esperar

            # Enviar solicitud al frontend
            self.socketio.emit("request_action", {
                "player_name": self.name,  # Identificar a quién se pide la acción
                "valid_actions": valid_actions,
                "hole_card": hole_card,
                "round_state": round_state
            },room=self.room_id)

            # Esperar a que el frontend envíe la acción vía socketio
            # Timeout opcional para evitar bloqueo infinito si el usuario se desconecta
            action_received = self.action_event.wait(
                timeout=300.0)  # Esperar hasta 5 minutos

            if not action_received or self.current_action_data is None:
                # Timeout o no se recibió acción válida del frontend
                print(
                    f"WARN: HumanPlayer {self.name} timed out or action not set. Folding.")
                # Buscar acción de fold en las válidas
                fold_action_obj = next(
                    (a for a in valid_actions if a['action'] == 'fold'), None)
                if fold_action_obj:
                    return fold_action_obj['action'], 0
                else:
                    # Muy raro: no se puede foldear? Devolver la primera acción válida (podría ser call 0)
                    fallback_action = valid_actions[0]['action'] if valid_actions else 'fold'
                    fallback_amount = valid_actions[0]['amount'] if valid_actions and fallback_action != 'fold' else 0
                    if isinstance(fallback_amount, dict):  # Si es raise, tomar el mínimo
                        fallback_amount = fallback_amount.get('min', 0)
                        if fallback_amount == -1:
                            fallback_amount = 0  # No deberia pasar si es primera accion
                    return fallback_action, fallback_amount

            # --- Validación de la Acción Recibida ---
            raw_action = self.current_action_data.get('action')
            raw_amount = self.current_action_data.get('amount')

            print(
                f"HumanPlayer {self.name} received raw action: {raw_action}, amount: {raw_amount}")

            validated_action = None
            validated_amount = 0

            for va in valid_actions:
                if va['action'] == raw_action:
                    # Acción encontrada, validar monto
                    if raw_action == 'fold':
                        validated_action = va['action']
                        validated_amount = 0  # El monto de fold es 0
                        break
                    elif raw_action == 'call':
                        # El monto debe coincidir EXACTAMENTE con el de la acción 'call' válida
                        # Esto cubre tanto check (amount 0) como call (amount > 0)
                        if va['amount'] == raw_amount:
                            validated_action = va['action']
                            # Usar el monto validado
                            validated_amount = va['amount']
                            break
                        # Si el monto no coincide (ej, usuario manda call -1), es inválido
                    elif raw_action == 'raise':
                        min_raise = va['amount']['min']
                        max_raise = va['amount']['max']
                        # Verificar que el raise sea posible (min != -1)
                        # y que el monto del usuario esté en el rango
                        if min_raise != -1 and isinstance(raw_amount, (int, float)) and min_raise <= raw_amount <= max_raise:
                            validated_action = va['action']
                            validated_amount = raw_amount  # Usar el monto válido elegido por el usuario
                            break
                        # Si min_raise es -1 o el monto está fuera de rango, es inválido

            if validated_action is not None:
                # ¡Acción válida! Salir del bucle y devolver
                print(
                    f"HumanPlayer {self.name} validated action: {validated_action}, amount: {validated_amount}")
                # No necesitamos limpiar el evento aquí, ya se hizo al inicio del loop
                return validated_action, validated_amount
            else:
                # Acción inválida, informar al frontend y volver a pedir
                print(
                    f"ERROR: HumanPlayer {self.name} submitted invalid action/amount: {raw_action}, {raw_amount}. Re-requesting.")
                self.socketio.emit("invalid_action", {
                    "message": f"Invalid action '{raw_action}' or amount '{raw_amount}'. Please choose again.",
                    "player_name": self.name,
                    "received_action": raw_action,
                    "received_amount": raw_amount,
                    "valid_actions": valid_actions  # Reenviar opciones válidas
                },room=self.room_id)
                # El bucle while continuará y volverá a esperar

    def receive_player_action(self, action_data):
        """
        Método llamado por el manejador de SocketIO cuando llega una acción del frontend.
        Espera un diccionario como {'action': 'raise', 'amount': 50}.
        """
        if isinstance(action_data, dict) and 'action' in action_data and 'amount' in action_data:
            # Convertir monto a int si es posible, manejar errores si no
            try:
                amount_val = action_data['amount']
                # Permitir None o valores numéricos
                if amount_val is not None:
                    amount_val = int(float(amount_val))
                # Si la acción es fold, forzar amount a 0
                if action_data['action'] == 'fold':
                    amount_val = 0

                self.current_action_data = {
                    'action': action_data['action'], 'amount': amount_val}
                print(
                    f"HumanPlayer {self.name} received action data: {self.current_action_data}")
                self.action_event.set()  # Avisar a declare_action que llegó una acción
            except (ValueError, TypeError) as e:
                print(
                    f"ERROR: HumanPlayer {self.name} received invalid amount type: {action_data.get('amount')}. Error: {e}")
                # No activar el evento si el monto es inválido
                self.socketio.emit("invalid_action", {
                    "message": f"Invalid amount format received: {action_data.get('amount')}. Amount must be a number.",
                    "player_name": self.name,
                },room=self.room_id)
        else:
            print(
                f"ERROR: HumanPlayer {self.name} received malformed action data: {action_data}")
            # Opcional: Informar al usuario del error
            self.socketio.emit("invalid_action", {
                "message": f"Malformed action data received from client.",
                "player_name": self.name,
            },room=self.room_id)

    def receive_game_start_message(self, game_info):
        # Enviar solo la información relevante, no todo el objeto si es muy grande
        simple_game_info = {
            "max_round": game_info.get("rule", {}).get("max_round"),
            "initial_stack": game_info.get("rule", {}).get("initial_stack"),
            "small_blind": game_info.get("rule", {}).get("small_blind_amount"),
            "ante": game_info.get("rule", {}).get("ante"),
            "players": len(game_info.get("seats", [])),
        }
        self.socketio.emit(
            "game_start", {"message": f"New game started!", "game_info": simple_game_info},room=self.room_id)

    def receive_round_start_message(self, round_count, hole_card, seats):
        self.hole_card = hole_card
        self.socketio.emit("round_start", {"round_count": round_count, 'seats': seats, 'hole_cards': {
                           'name': self.name, 'cards': hole_card}},room=self.room_id)

    def receive_street_start_message(self, street, round_state):
        self.socketio.emit(
            "street_start", {"street": street, "round_state": round_state},room=self.room_id)

    def receive_game_update_message(self, action, round_state):
        self.socketio.emit(
            "game_update", {"action": action, "round_state": round_state},room=self.room_id)

    def receive_round_result_message(self, winners, hand_info, round_state):
        # El wait/clear aquí es problemático y puede bloquear el motor.
        # La UI debería manejar la visualización del resultado sin bloquear al backend.
        # Si necesitas una pausa o confirmación del usuario, la UI debe gestionarla
        # y, si acaso, enviar un evento separado al servidor cuando esté lista,
        # pero ese evento NO debería usar self.action_event.
        win = any(self.name == win['name'] for win in winners)
        if win:
            print(f"HumanPlayer {self.name} received round result.")
            # self.socketio.emit("round_result", {
            #                    "winners": winners, "hand_info": hand_info, "round_state": round_state},room=self.room_id)
            self.socketio.emit("winners", {"winners": winners},room=self.room_id)
      
