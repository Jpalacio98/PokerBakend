from flask_socketio import emit, join_room, leave_room
from flask import request
# Asume que estas funciones existen
from app.game.engine import start_game_poker, config_game
# Asegúrate de que HumanPlayer sea accesible o esté dentro de engine
from app.game.engine import human # O donde sea que esté HumanPlayer
from app.game import eval_had, get_weight  # Asume que estas funciones existen
import eventlet
from app.services.user_services import UserService
from app.extensions import active_rooms
from app.game.engine import get_app

def setup_websocket_events(socketio):
    """Registra los eventos WebSocket con gestión de salas"""

    @socketio.on("connect")
    def handle_connect():
        user_sid = request.sid
        print(f'User connected: {user_sid}')
        # Cada usuario se une a su propia sala privada identificada por su SID
        join_room_game(user_sid)

    @socketio.on("disconnect")
    def handle_disconnect():
        user_sid = request.sid
        print(f'User disconnected: {user_sid}')

        if user_sid in active_rooms:
            # Intentar detener el hilo del juego si está activo
            active_rooms[user_sid]['userservice'].game_stop()
            game_thread = active_rooms[user_sid].get('game_thread')
            if game_thread:
                print(
                    f"Intentando detener el hilo del juego para la sala {user_sid}...")
                # eventlet.kill() es una forma abrupta, idealmente el juego
                # debería tener un mecanismo para detenerse limpiamente.
                try:
                    game_thread.kill()  # Matar el greenlet
                    print(f"Hilo para sala {user_sid} detenido.")
                except Exception as e:
                    print(
                        f"Error al detener el hilo para sala {user_sid}: {e}")

            # Limpiar la información de la sala
            del active_rooms[user_sid]
            print(f"Sala {user_sid} eliminada.")

        # leave_room(user_sid) # Ocurre automáticamente al desconectar

        # Ya no se notifica globalmente, la desconexión es individual.
        # Puedes registrarlo en el servidor si es necesario.
        # socketio.emit("server_response", {"message": "Un usuario se ha desconectado."}) # <-- Evitar esto

    def join_room_game(user_sid):
        join_room(user_sid)
        print(f'User {user_sid} joined room {user_sid}')

        # Inicializar estado para esta nueva sala (usuario)
        active_rooms[user_sid] = {
            'sid': user_sid,
            'game_thread': None,
            'config': None,
            'human_player': None  # Placeholder para el objeto HumanPlayer
        }

        # Enviar respuesta solo al usuario que se conectó
        socketio.emit("server_response", {
            "message": f"¡Conectado! Tu sala privada es {user_sid}", "roomId": user_sid},
            room=user_sid)  # Usar room=user_sid o to=user_sid
    # --- Eventos relacionados con el juego (ahora específicos de la sala) ---
    @socketio.on("set_config")
    def handle_set_config(data):
        user_sid = request.sid
        if user_sid not in active_rooms:
            join_room_game(user_sid)
            print(f"Error: Sala {user_sid} no encontrada para set_config.")
            socketio.emit(
                'error', {'message': 'Error de sesión, por favor reconecta.'}, room=user_sid)
            

        
        try:

            players_list = config_game(socketio, data['table'], data['name'], user_sid)

            # 1. Guardar la configuración cruda
            config_data = {'table': data['table'], 'name': data['name']}
            active_rooms[user_sid]['config'] = config_data
            # 2. Crear el jugador humano AHORA y guardarlo
            active_rooms[user_sid]['human_player'] = data['name']
            # 3. Guarda en la  bd
            active_rooms[user_sid]['userservice'] = UserService()
            print(data['table'])
            active_rooms[user_sid]['userservice'].create_game(data['table']['id'])
            active_rooms[user_sid]['userservice'].pay_stack(data['table'],data['name'])
            # Guardar lista para referencia si es necesario
            active_rooms[user_sid]['players'] = players_list

            # emitir la lista de jugadores SÓLO a la sala del usuario
            socketio.emit('get_players', {
                          'players': players_list}, room=user_sid)
            # print(f"Configuración lista para sala {user_sid}")
            # print("lista de jugadores",players_list)
            print(f"Configurando juego para sala {user_sid} con data: {data}")
            
        except Exception as e:
            print(f"Error en handle_set_config para sala {user_sid}: {e}")
            socketio.emit(
                'error', {'message': f'Error al configurar el juego: {e}'}, room=user_sid)

    @socketio.on("start_game")
    def handle_start_game(data):
        shared_app = get_app()
        if not shared_app:
            raise RuntimeError("shared_app aún no está inicializada")
        user_sid = request.sid
        print(data.get("username"))
        if user_sid not in active_rooms:
            print(f"Error: Sala {user_sid} no encontrada para start_game.")
            socketio.emit(
                'error', {'message': 'Error de sesión, por favor reconecta.'}, room=user_sid)
            return

        if not active_rooms[user_sid].get('config'):
            print(f"Error: Juego no configurado para sala {user_sid}.")
            socketio.emit(
                'error', {'message': 'Debes configurar el juego primero.'}, room=user_sid)
            return

        if active_rooms[user_sid].get('game_thread') is not None:
            print(f"Advertencia: Juego ya iniciado en sala {user_sid}.")
            socketio.emit('server_response', {
                          'message': 'El juego ya está en curso.'}, room=user_sid)
            return

        print(f"Iniciando hilo de juego para sala {user_sid}")
        # Ejecuta el juego en un hilo separado, pasando socketio y el ID de la sala
        # Asume que start_game_poker está adaptada para usar room_id
        game_thread = eventlet.spawn(start_game_poker, socketio, user_sid,data.get("username"))
        # Guardar referencia al hilo
        active_rooms[user_sid]['game_thread'] = game_thread

        # Notificar SÓLO al usuario de esa sala
        socketio.emit("server_response", {
                      "message": "Juego iniciado en un hilo separado para tu sala."}, room=user_sid)
        print("sala finalizada")

    @socketio.on("test")
    def handle_test(data):
        user_sid = request.sid
        print(f"Mensaje de prueba recibido de {user_sid}: {data['message']}")
        # Responder SÓLO al usuario que envió el test
        socketio.emit("server_response", {
                      "message": "El servidor te escuchó y responde este mensaje (privado)."}, room=user_sid)

    # --- Eventos relacionados con el jugador (ahora específicos de la sala) ---
    @socketio.on("player_action")
    def handle_player_action(data):
        from app.game.engine import human 
        user_sid = request.sid
        if user_sid not in active_rooms or not active_rooms[user_sid].get('human_player'):
            print(
                f"Error: Sala {user_sid} o jugador no encontrado para player_action.")
            # Podrías socketio.emitir un error o simplemente ignorar
            return

        action, amount = data["action"], data["amount"]
#         
        print(f"Sala {user_sid} - Acción recibida: {action}, Monto: {amount}")
        # Enviar la acción al objeto HumanPlayer correcto asociado a esta sala
        # Necesitas que tu HumanPlayer tenga un método para recibir/procesar esto
        # y que el hilo del juego (start_game_poker) espere esta acción.
        try:
            # Esta es la parte CRÍTICA: HumanPlayer debe tener un mecanismo
            # para que el hilo del juego espere y reciba esta acción.
            # Puede ser una cola interna, un eventlet.Event, etc.
            # Asume que este método existe y funciona
           human.receive_player_action(data)
        except Exception as e:
            print(
                f"Error al procesar acción del jugador en sala {user_sid}: {e}")
            socketio.emit(
                'error', {'message': 'Error procesando tu acción.'}, room=user_sid)

    @socketio.on("start_next_round")
    def handle_start_next_round():
        from app.game.engine import dealer 
        user_sid = request.sid
        if user_sid not in active_rooms or not active_rooms[user_sid].get('human_player'):
            print(
                f"Error: Sala {user_sid} o jugador no encontrado para start_next_round.")
            return

        
        print(f"Sala {user_sid} - Solicitud para iniciar siguiente ronda.")
        # Similar a player_action, necesitas un mecanismo en HumanPlayer o
        # en el bucle del juego para manejar esta señal.
        try:
            dealer.next_round()  # Asume que existe un método así
        except Exception as e:
            print(f"Error al señalar siguiente ronda en sala {user_sid}: {e}")
            socketio.emit(
                'error', {'message': 'Error iniciando siguiente ronda.'}, room=user_sid)
            
    @socketio.on("starter")
    def handle_starter(data):
        from app.game.engine import dealer 
        user_sid = request.sid
        if user_sid not in active_rooms or not active_rooms[user_sid].get('human_player'):
            print(
                f"Error: Sala {user_sid} o jugador no encontrado para start_next_round.")
            return

       
        try:
            type = data.get("type")
            if type == "game":
                dealer.starter_game()  # Asume que existe un método así
            else:
                dealer.starter_round()
        except Exception as e:
            print(f"Error al señalar siguiente ronda en sala {user_sid}: {e}")
            socketio.emit(
                'error', {'message': 'Error iniciando siguiente ronda.'}, room=user_sid)
            
    @socketio.on("start_new_game")
    def handle_start_new_game():
        from app.game.engine import dealer 
        user_sid = request.sid
        if user_sid not in active_rooms or not active_rooms[user_sid].get('human_player'):
            print(
                f"Error: Sala {user_sid} o jugador no encontrado para start_next_round.")
            return

        if active_rooms[user_sid].get('game_thread') is not None:
            leave_room(user_sid)
            active_rooms[user_sid]['game_thread'].kill()
            print("ejecuacion del juego terminada")
        print(f"Sala {user_sid} - Solicitud para iniciar siguiente Partida.")
        # Similar a player_action, necesitas un mecanismo en HumanPlayer o
        # en el bucle del juego para manejar esta señal.
        try:
            dealer.next_game()  # Asume que existe un método así
            active_rooms.pop(user_sid)
            socketio.emit("new_game")
        except Exception as e:
            print(f"Error al señalar siguiente partida en sala {user_sid}: {e}")
            socketio.emit(
                'error', {'message': 'Error iniciando siguiente patida.'}, room=user_sid)
            

    @socketio.on("eval_cards")
    def handle_eval_cards(data):
        user_sid = request.sid
        # Esta función parece ser puramente calculadora, no depende del estado del juego
        # por lo que no necesita acceder a active_rooms más que para responder.
        print(f"Sala {user_sid} - Evaluando cartas: {data}")
        try:
            hole, community = data["hole"], data["community"]
            # Asume que eval_had y get_weight son funciones puras
            hand = eval_had(hole, community)
            hand_weight = get_weight(hand['strength'])
            res = {'strength': hand['strength'],
                   'hand_value': hand['hand_value'], 'weight': hand_weight}
            print(f"Resultado evaluación para {user_sid}: {res}")
            # Enviar el resultado SÓLO al usuario que lo solicitó
            socketio.emit("get_strength", res, room=user_sid)
        except Exception as e:
            print(f"Error en handle_eval_cards para sala {user_sid}: {e}")
            socketio.emit(
                'error', {'message': f'Error evaluando cartas: {e}'}, room=user_sid)
