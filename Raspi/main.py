# =======================================================================
#                         🔹 O N Y X - P R O 🔹
# =======================================================================
#  Archivo   : main.py
#  Autor     : Klaus Michalsky
#  Fecha     : Oct-2026
# -----------------------------------------------------------------------
#  ▫️ DESCRIPCIÓN
#     - Control principal de ONYX-Pro
#     - Gestión de partida de ajedrez
#     - Comunicación con RP2040
#     - Control de Stockfish
# =======================================================================


import signal

import sensors

from robot import (
    do_homing,
    shutdown_robot,
    execute_robot_move,
    initialize_robot,
    clear_input_buffer,
    initialize_serial,
)

from stockfish import (
    initialize_stockfish,
    get_best_move,
    shutdown_stockfish,
)

from game import (
    create_board,
    process_human_move,
    push_move,
    is_game_over,
    get_result,
    mirror_move,
    sensor_occupancy_from_board,
    prepare_robot_move,
)

initialize_serial()

initialize_stockfish()

initialize_robot()

board = create_board()


# =========================
# SHUTDOWN
# =========================

def shutdown():
    """Cierra los sensores, Stockfish y el robot."""
    sensors.shutdown_sensors()
    shutdown_stockfish()
    shutdown_robot()


def handle_interrupt(signum, frame):
    # Al pulsar Ctrl+C, se ejecutará el apagado del robot y se cerrará la conexión serie
    print("\n⚠️ Interrupción: apagando ONYX-Pro...")
    shutdown()
    raise SystemExit(130)


signal.signal(signal.SIGINT, handle_interrupt)


# =========================
# START
# =========================


print("🤖 ONYX-Pro READY")

do_homing()

# strip() es un método de un objeto str elimina espacios en blanco al inicio y al final de la cadena de texto.
mode = input("\n¿Quién empieza? (1=Humano, 2=Robot): ").strip()
human_turn = (mode == "1")
# Así, mirror_coordinates será True cuando empiece el humano y False cuando empiece el robot
mirror_coordinates = (mode == "1")

# =========================
# SENSORES Y BOTÓN
# =========================

expected_state = sensor_occupancy_from_board(
    board,
    mirror_coordinates,
)

confirmed_state = sensors.initialize_and_validate_sensors(
    expected_state,
)

change_history = []

print("\n♟️ Iniciando partida...\n")


# =========================
# LOOP PRINCIPAL
# =========================

while True:

    # =====================
    # TURNO HUMANO
    # =====================

    if human_turn:

        print("\n♟️ Mové tus piezas y pulsá el botón para confirmar.")
        print("Podés corregir tus movimientos antes de confirmar.")

        while True:

            # Esperar a que se pulse el botón y obtener el estado del tablero.
            current_state = sensors.wait_for_human_confirmation(
                confirmed_state,
                change_history,
            )

            # Si el tablero volvió a la posición confirmada.
            if current_state is None:
                print("↩️ Tablero restaurado. Podés volver a mover.")
                continue

            try:
                # Identificar y validar la jugada humana.
                logical_move, human_move = process_human_move(
                    board,
                    confirmed_state,
                    current_state,
                    change_history,
                    mirror_coordinates,
                )

            except (ValueError, IndexError) as error:
                print(f"❌ Jugada no confirmada: {error}")
                print("Corregí las piezas y volvé a pulsar.")
                continue

            # Mostrar las coordenadas físicas y lógicas.
            physical_move = (
                mirror_move(logical_move)
                if mirror_coordinates
                else logical_move
            )

            push_move(board, human_move)

            print("👤 Human_Physical_Board:", physical_move)
            print("👤 Human_Stockfish_Board:", logical_move)

            # Guardar la posición confirmada.
            confirmed_state = current_state.copy()
            change_history.clear()

            human_turn = False
            break

    # =====================
    # TURNO ROBOT
    # =====================
    else:

        # Limpiar mensajes anteriores del buffer de entrada del puerto serie.
        clear_input_buffer()

        # Stockfish calcula su mejor jugada usando las coordenadas lógicas.
        stockfish_move = get_best_move(board)

        # Preparar la jugada lógica, las coordenadas físicas
        # y los datos necesarios si hay una captura.
        move, robot_move, capture_square, from_square = prepare_robot_move(
            board,
            stockfish_move,
            mirror_coordinates,
        )

        print("🤖 Robot_Stockfish_Board:", stockfish_move)
        print("🤖 Robot_Physical_Board:", robot_move)

        # =====================
        # EJECUTAR MOVIMIENTO
        # =====================

        if capture_square is not None and from_square is not None:
            execute_robot_move(
                robot_move,
                capture_square,
                from_square,
            )
        else:
            execute_robot_move(robot_move)

        # Actualizar el tablero lógico con la jugada original de Stockfish.
        push_move(board, move)

        # Sincronizar sensores después del movimiento del robot.
        confirmed_state = sensors.read_stable_sensor_state()

        expected_state = sensor_occupancy_from_board(
            board,
            mirror_coordinates,
        )

        confirmed_state = sensors.synchronize_board(
            expected_state,
            confirmed_state,
            change_history,
        )

        # Cambiar el turno al humano.
        human_turn = True

    # =====================
    # FIN PARTIDA
    # =====================

    if is_game_over(board):

        print("\n🏁 Fin de partida")
        print(get_result(board))

        shutdown()
        break
