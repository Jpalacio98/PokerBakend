¡Excelente idea! Crear niveles de dificultad progresiva para tus bots de poker es una forma fantástica de mejorar la experiencia de juego. Aquí te presento un enfoque escalonado, desde lo más simple hasta lo más complejo, utilizando técnicas que se pueden implementar de forma incremental en `pypokerengine`.

**Filosofía General:**

Empezaremos con cambios muy básicos y añadiremos capas de lógica en cada nivel. Nos centraremos en:

1.  **Selección de Manos Pre-flop:** Qué manos jugar y cuáles descartar antes del flop.
2.  **Agresividad:** Cuándo apostar/subir vs. pasar/igualar.
3.  **Evaluación Post-flop:** Cómo jugar después de ver el flop, turn y river.
4.  **Posición:** Jugar diferente según si actúas de los primeros o de los últimos.
5.  **Tamaño de Apuestas:** Apostar cantidades más significativas y estratégicas.
6.  **(Opcional Avanzado):** Lectura básica de oponentes y faroles (bluffs).

**Técnicas Propuestas y Aplicación por Nivel:**

Aquí tienes un plan detallado para cada nivel, aumentando la "inteligencia" gradualmente:

---

**Nivel 1: Novice (Tu Bot Actual)**

*   **Técnica:** Aleatoriedad Pura.
*   **Implementación:** Ya lo tienes. El bot elige una acción válida al azar y, si es subir (`raise`), elige un monto al azar dentro del rango permitido. No considera sus cartas, la mesa, ni nada.
*   **Comportamiento:** Impredecible pero sin ninguna estrategia. Juega demasiadas manos débiles y no sabe cuándo apostar fuerte con manos buenas.

---

**Nivel 2: Apprentice**

*   **Técnica:** Selección Pre-flop Ultra-Básica.
*   **Implementación:**
    *   Introduce un umbral mínimo de calidad para las cartas iniciales (`hole_card`).
    *   Usa una función simple para evaluar la fuerza inicial (ej: pares, cartas altas conectadas o del mismo palo).
    *   Si las cartas son muy malas (ej: 7-2 offsuit, 9-4 offsuit), **siempre** elige `fold` si es posible. Si la opción es `check` (pasar), la toma.
    *   Si las cartas superan el umbral mínimo, actúa aleatoriamente como el Nivel 1.
*   **Comportamiento:** Evita las peores manos iniciales, pero sigue siendo muy aleatorio después. Un pequeño paso hacia la sensatez.

---

**Nivel 3: Enthusiast**

*   **Técnica:** Selección Pre-flop Mejorada + Lógica Post-flop Básica (Hit-or-Fold).
*   **Implementación:**
    *   Usa una tabla de manos iniciales un poco más refinada (ej: Sistema de Chen o Sklansky-Karlson simplificado) para decidir si jugar pre-flop.
    *   **Post-flop:** Después del flop, turn o river:
        *   Evalúa la mejor mano posible con sus `hole_card` y las `community_card` (necesitarás una función `eval_hand`).
        *   Si tiene un par (usando una de sus cartas) o algo mejor (doble par, trío, etc.): Tiende a elegir `call` o `raise` (aleatoriamente entre ellas si ambas son válidas).
        *   Si no tiene ni un par (carta alta): Tiende a elegir `check` o `fold`.
    *   Sigue usando tamaños de apuesta aleatorios para `raise`.
*   **Comportamiento:** Juega manos iniciales más razonables y no sigue apostando post-flop si no ha ligado nada. Aún es pasivo y predecible.

---

**Nivel 4: Casual Player**

*   **Técnica:** Conciencia de Posición Pre-flop + Apuestas por Valor Básicas.
*   **Implementación:**
    *   **Posición:** Divide las posiciones en la mesa (temprana, media, tardía). Juega un rango de manos más estricto (más fuerte) en posiciones tempranas y un rango más amplio en posiciones tardías (como el botón).
    *   **Apuestas por Valor:**
        *   Pre-flop: Si tiene una mano *muy* fuerte (ej: AA, KK, QQ, AK), tiende a elegir `raise` en lugar de `call`.
        *   Post-flop: Si tiene una mano fuerte (ej: doble par, trío o mejor), tiende a elegir `raise` y a usar un tamaño de apuesta mayor (ej: 50%-100% del rango `amount["max"]` permitido para `raise`, en lugar de totalmente aleatorio). Si tiene una mano media (par alto), tiende a `call`. Si no liga nada, `check`/`fold`.
*   **Comportamiento:** Empieza a jugar estratégicamente según su posición y a extraer más valor de sus manos fuertes.

---

**Nivel 5: Expert Player**

*   **Técnica:** Consideración de Proyectos (Draws) + Tamaño de Apuesta Proporcional al Bote.
*   **Implementación:**
    *   **Proyectos:** Identifica proyectos fuertes post-flop (proyecto de color con 4 cartas del mismo palo, proyecto de escalera abierta con 4 cartas consecutivas).
    *   Si tiene un proyecto fuerte, está dispuesto a hacer `call` a apuestas razonables (ej: no más de 1/2 o 1/3 del bote actual). Ya no hace `fold` automáticamente si no ha ligado.
    *   **Tamaño de Apuesta:** Cuando apuesta por valor (con manos hechas fuertes), en lugar de un monto aleatorio, calcula un tamaño relativo al bote (ej: apostar entre 1/2 y 3/4 del tamaño del bote actual, asegurándose que esté dentro de `valid_actions`). Si `raise` es la acción, el monto a añadir debe considerar el bote.
*   **Comportamiento:** Juega proyectos de forma más correcta y sus apuestas empiezan a tener un tamaño más estándar y lógico. Menos explotable.

---

**Nivel 6: Shark**

*   **Técnica:** Agresividad Selectiva (Semi-Farol) + Apuesta de Continuación (C-Bet).
*   **Implementación:**
    *   **Semi-Farol:** Si tiene un proyecto fuerte (como en Nivel 5), *a veces* elige `raise` en lugar de solo `call`, especialmente si fue el agresor pre-flop o está en posición tardía.
    *   **Apuesta de Continuación:** Si el bot fue el último en hacer `raise` pre-flop, tiende a hacer una apuesta (un `bet` si nadie ha apostado aún) en el flop, *incluso si no ligó nada*, aproximadamente un 50-70% de las veces. El tamaño sería moderado (ej: 1/3 a 1/2 del bote).
*   **Comportamiento:** Más agresivo y difícil de leer. Gana botes sin necesidad de tener la mejor mano, aplicando presión.

---

**Nivel 7: Local Legend**

*   **Técnica:** Adaptación Básica a la Acción + Refinamiento de Rangos.
*   **Implementación:**
    *   **Adaptación a la Acción:** Considera cuántos jugadores hay en la mano y si hubo muchas subidas (`raise`) pre-flop. Juega un rango más ajustado si hay muchas subidas o muchos jugadores. Post-flop, es más cauteloso si un jugador previamente pasivo de repente apuesta fuerte.
    *   **Refinamiento de Rangos:** Usa tablas de manos pre-flop más detalladas que consideren no solo la posición sino también si alguien ya subió antes.
    *   Post-flop: Empieza a diferenciar la fuerza de su mano (par bajo vs. par alto vs. top pair top kicker) y ajusta su disposición a apostar/pagar.
*   **Comportamiento:** Juega de forma más sólida en mesas multi-jugador y reacciona de forma más lógica a la agresividad de los oponentes.

---

**Nivel 8: National Champion**

*   **Técnica:** Conciencia del Stack + Faroles Puros Ocasionales.
*   **Implementación:**
    *   **Conciencia del Stack (Stack Awareness):** Considera su propio tamaño de stack y el de los oponentes activos.
        *   Si está corto de fichas (ej: < 20 ciegas grandes), juega un estilo más "push/fold" pre-flop (o va all-in o se retira).
        *   Evita meter muchas fichas en faroles contra jugadores con stacks muy pequeños (que probablemente pagarán).
    *   **Faroles Puros:** En situaciones específicas (ej: en el river, cuando los proyectos no se completaron en la mesa, y está contra un solo oponente que ha mostrado debilidad - pasando dos veces), puede intentar un farol puro (apostar sin tener nada) un pequeño porcentaje de las veces.
*   **Comportamiento:** Adapta su estrategia a la fase del torneo/partida (implícito por los stacks) y añade faroles calculados a su arsenal.

---

**Nivel 9: Grand Poker Master**

*   **Técnica:** Explotación Básica de Oponentes + Check-Raising.
*   **Implementación:**
    *   **(Requiere guardar estado simple):** El bot necesita recordar *algo* sobre las acciones de los oponentes en la mano actual o rondas recientes.
        *   Si un oponente específico se retira (`fold`) mucho ante las apuestas de continuación (C-Bets), el bot aumenta la frecuencia de sus C-Bets contra ese jugador.
        *   Si un oponente parece muy agresivo, el bot ajusta su rango para pagar (`call`) o re-subir (`raise`) siendo más fuerte.
    *   **Check-Raising:** En posición (actuando después del oponente), si tiene una mano muy fuerte o un buen proyecto con semi-farol, puede elegir `check` inicialmente, esperando que el oponente apueste, para luego hacer `raise`. Lo hace ocasionalmente para variar su juego.
*   **Comportamiento:** Empieza a desviarse de una estrategia fija para explotar tendencias percibidas en los oponentes. Más impredecible y peligroso.

---

**Nivel 10: Poker Legend**

*   **Técnica:** Juego Equilibrado + Conceptos Avanzados (Blockers, Meta-juego simple).
*   **Implementación:**
    *   **Equilibrio:** Intenta equilibrar sus rangos. Por ejemplo, no *siempre* hace check-raise con manos monstruo; a veces solo paga o apuesta directamente. No *siempre* hace C-Bet con aire; a veces se rinde. Esto lo hace mucho más difícil de leer.
    *   **Blockers:** Considera sus propias cartas (`hole_card`) para determinar qué tan probable es que el oponente tenga ciertas manos fuertes. (Ej: si tiene el As de picas en una mesa con 3 picas, es menos probable que el oponente tenga el color máximo). Usa esta información para decidir si farolear o pagar.
    *   **Meta-juego Simple:** Si ha estado jugando muy agresivo, puede jugar una mano fuerte de forma pasiva para inducir acción. Si ha estado jugando pasivo, puede intentar un farol audaz. (Requiere más estado).
    *   **(Opcional muy avanzado):** Podría incorporar cálculos de Equity vs Rango (estimar la probabilidad de ganar contra el rango de manos probable del oponente) usando librerías externas o simplificaciones. O incluso simulaciones Monte Carlo si el tiempo lo permite (poco probable en `declare_action`).
*   **Comportamiento:** El bot más duro. Difícil de leer, adapta su juego, y utiliza conceptos avanzados para tomar decisiones marginales. Se acerca a un juego sólido y potencialmente explotador.

---

**Implementación Práctica:**

1.  **Clases Separadas:** Crea una clase Python para cada nivel (ej: `ApprenticePlayer(BasePokerPlayer)`, `EnthusiastPlayer(BasePokerPlayer)`, etc.). Puedes hacer que hereden de la anterior para reutilizar código, o tener una clase base común con la lógica compartida.
2.  **Funciones de Ayuda:** Necesitarás funciones auxiliares:
    *   `eval_hand(hole_cards, community_cards)`: Devuelve la fuerza de la mano (par, doble par, trío, color, etc.) y quizás su ranking numérico.
    *   `get_preflop_strength(hole_cards)`: Evalúa la fuerza inicial.
    *   `get_position(seats, my_uuid)`: Determina si estás en posición temprana, media o tardía.
    *   `calculate_pot_size(round_state)`: Calcula el tamaño actual del bote.
    *   (Para niveles avanzados) Funciones para identificar proyectos, evaluar rangos de oponentes (muy simplificado), etc.
3.  **Estado:** Para los niveles más avanzados (7+), necesitarás que tu clase de bot almacene algo de información entre llamadas a `declare_action` (ej: `self.aggresor_preflop = True`, `self.opponent_fold_rate[opponent_uuid] = ...`). Ten cuidado con cómo se resetea esta información entre rondas o manos.
4.  **Parámetros:** En lugar de lógica fija (ej: "apostar 50%"), usa parámetros (ej: `self.value_bet_size_ratio = 0.5`) que puedan ser diferentes para cada nivel de bot.

Empieza implementando los primeros niveles. Cada paso te dará un bot notablemente mejor que el anterior. ¡Mucha suerte!