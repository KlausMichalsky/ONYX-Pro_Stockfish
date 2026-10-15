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

import time

import sensors

from robot import (
    ser,
    reset_robot,
    send_to_robot,
    wait_done,
    do_homing,
    wait_any,
    shutdown_robot,
)
from stockfish import (
    get_best_move,
    shutdown_stockfish,
)

from game import (
    create_board,
    create_move,
    validate_human_move,
    push_move,
    is_capture,
    get_capture_squares,
    is_game_over,
    get_result,
    mirror_square,
    mirror_move,
    detect_human_move,
    _sensor_occupancy_from_board,
)

print("Reset RP2040...")
reset_robot()

board = create_board()

# pausa de 1 segundo;
# motivo específico en este programa todavía no identificado
# time.sleep(1)


# =========================
# SHUTDOWN
# =========================

def shutdown():
    # para que también cierre los sensores y el botón
    if sensors.button is not None:
        sensors.button.close()

    if sensors.i2c is not None:
        sensors.i2c.close()

    shutdown_stockfish()
    shutdown_robot()


# =========================
# Lectura Estable de Sensores
# =========================

def read_stable_sensor_state():
    """Espera hasta leer el mismo estado 3 veces consecutivas."""
    last_state = None
    stable_reads = 0

    for _ in range(20):
        sensors.detect_changes()
        current_state = sensors.board_state.copy()

        if current_state == last_state:
            stable_reads += 1
        else:
            last_state = current_state
            stable_reads = 1

        if stable_reads >= 3:
            return current_state

        time.sleep(0.05)

    raise RuntimeError(
        "Los sensores no se estabilizaron después de varios intentos."
    )


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

sensors.init_sensors()

confirmed_state = read_stable_sensor_state()

expected_state = _sensor_occupancy_from_board(
    board, mirror_coordinates
)

if confirmed_state != expected_state:
    print("❌ Los sensores no coinciden con la posición inicial.")
    shutdown()
    raise SystemExit(1)

change_history = []

print("✅ Sensores y botón listos")

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

            # Registrar los cambios detectados por los sensores.
            change_history.extend(sensors.detect_changes())

            if sensors.button_pressed():

                sensors.wait_button_release()

                # Leer los últimos cambios antes de confirmar.
                change_history.extend(sensors.detect_changes())
                current_state = sensors.board_state.copy()

                try:
                    # Identificar la jugada final usando el estado
                    # inicial, el estado actual y el historial.
                    logical_move = detect_human_move(
                        board,
                        confirmed_state,
                        current_state,
                        change_history,
                        mirror_coordinates,
                    )

                    # Validar la jugada contra el tablero lógico.
                    human_move = validate_human_move(
                        board, logical_move
                    )

                    if human_move is None:
                        print("❌ Jugada ilegal. Corregí las piezas.")
                        continue

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

            time.sleep(0.05)

    # =====================
    # TURNO ROBOT
    # =====================

    else:

        # Limpiar mensajes anteriores del buffer de entrada del puerto serie
        ser.reset_input_buffer()

        # El board contiene la posición actual de la partida.
        # Stockfish calcula su mejor jugada usando las coordenadas lógicas del tablero.
        stockfish_move = get_best_move(board)

        # Convertir la jugada en texto UCI a un objeto Move de python-chess.
        # Este objeto se utiliza para comprobar capturas y actualizar el tablero.
        move = create_move(stockfish_move)

        # Mostrar la jugada original calculada por Stockfish, sin reflejar.
        print("🤖 Robot_Stockfish_Board:", stockfish_move)

        # Reflejar las coordenadas para el tablero físico,
        # porque la orientación del tablero nunca cambia.
        robot_move = mirror_move(
            stockfish_move) if mirror_coordinates else stockfish_move

        # Mostrar la jugada que se enviará al RP2040.
        print("🤖 Robot_Physical_Board:", robot_move)

        # =====================
        # CAPTURA
        # =====================
        # Comprobar si la jugada de Stockfish captura una pieza.
        if is_capture(board, move):

            # Obtener las casillas de destino y origen de la captura.
            capture_square, from_square = get_capture_squares(move)

            # Reflejar ambas casillas si el tablero físico requiere transformación.
            if mirror_coordinates:
                capture_square = mirror_square(capture_square)
                from_square = mirror_square(from_square)

            # Enviar al RP2040 la orden para retirar la pieza capturada.
            send_to_robot(f"REMOVE {capture_square} {from_square}")

            # Esperar la confirmación del RP2040.
            wait_any("MOVE DONE", "CAPTURE DONE")

            print("✅ Captura completada")

        else:
            # Enviar al RP2040 la jugada transformada para el tablero físico.
            send_to_robot(robot_move)

            # Esperar a que el robot termine el movimiento.
            wait_done()

        # Actualizar el tablero lógico con la jugada original de Stockfish,
        # nunca con las coordenadas reflejadas del tablero físico.
        push_move(board, move)

        # Sincronizar sensores después del movimiento del robot.
        confirmed_state = read_stable_sensor_state()
        change_history.clear()

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
