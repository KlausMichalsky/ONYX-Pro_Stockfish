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
    shutdown_stockfish()
    shutdown_robot()


# =========================
# START
# =========================

print("🤖 ONYX-Pro READY")

do_homing()

# strip() es un método de un objeto str elimina espacios en blanco al inicio y al final de la cadena de texto.
mode = input("¿Quién empieza? (1=Humano, 2=Robot): ").strip()
human_turn = (mode == "1")
# Así, mirror_coordinates será True cuando empiece el humano y False cuando empiece el robot
mirror_coordinates = (mode == "1")

print("\n♟️ Iniciando partida...\n")


# =========================
# LOOP PRINCIPAL
# =========================

while True:

    # =====================
    # TURNO HUMANO
    # =====================

    if human_turn:

        move = input("\n♟️ Tu jugada (ej: e2e4) | q = salir: ").strip().lower()

        if move == "q":
            print("👋 Saliendo...")
            shutdown()
            break

        try:
            logical_move = mirror_move(move) if mirror_coordinates else move
            human_move = validate_human_move(board, logical_move)

            if human_move is None:
                print("❌ Jugada ilegal")
                continue  # No sigas ejecutando esta vuelta del loop; vuelve directamente al principio del while

        except (ValueError, IndexError):
            print("❌ Formato inválido")
            continue

        push_move(board, human_move)

        print("👤 Human_Physical_Board:", move)
        print("👤 Human_Stockfish_Board:", logical_move)

        human_turn = False  # cambiar el turno al robot

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
