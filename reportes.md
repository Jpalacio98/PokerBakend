Reportes
Reporte de partidas jugadas por nivel (Filtrar por level_id en tables y game_sessions).

Reporte de ganancias y pérdidas de un usuario (Total de total_winnings en players por user_id).

Reporte de apuestas por jugador (Suma de amount en bets por player_id).

Reporte de manos ganadas por jugador (Conteo de winnings > 0 en hand_history).

Reporte de actividad de las mesas (Conteo de game_sessions por table_id).

Reporte de transacciones de los usuarios (Sumatoria de amount en transactions).

Reporte de jugadores en cada nivel (Conteo de players por level_id en tables).

Reporte de recaudación total del sistema (Sumatoria de amount en transactions donde transaction_type='buy-in').

Reporte de duración de partidas (Diferencia end_time - start_time en game_sessions).

Reporte de jugadores más activos (Conteo de bets por player_id).

Con esta nueva estructura, tu sistema podrá generar reportes detallados y mejorar la gestión de los datos. ¿Necesitas algún ajuste adicional?