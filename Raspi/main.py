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
)

print("Reset RP2040...")
reset_robot()

board = create_board()

time.sleep(1)


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

mode = input("¿Quién empieza? (1=Humano, 2=Robot): ").strip()
human_turn = (mode == "1")

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
            human_move = validate_human_move(board, move)

            if human_move is None:
                print("❌ Jugada ilegal")
                continue

        except ValueError:
            print("❌ Formato inválido")
            continue

        push_move(board, human_move)

        print("👤 Humano:", move)

    # =====================
    # TURNO ROBOT
    # =====================

    else:

        ser.reset_input_buffer()

        stockfish_move = get_best_move(board)
        move = create_move(stockfish_move)

        print("🤖 Stockfish:", stockfish_move)

        # =====================
        # CAPTURA
        # =====================
        if is_capture(board, move):

            capture_square, from_square = get_capture_squares(move)

            send_to_robot(f"REMOVE {capture_square} {from_square}")

            # 🔥 SOLO esperar final real del sistema completo
            # o "CAPTURE DONE + FINAL DONE" mejor aún
            wait_any("MOVE DONE", "CAPTURE DONE")

            print("✅ Captura completada")

        else:
            send_to_robot(stockfish_move)
            wait_done()

        push_move(board, move)

        human_turn = True

    # =====================
    # FIN PARTIDA
    # =====================

    if is_game_over(board):

        print("\n🏁 Fin de partida")
        print(get_result(board))

        shutdown()
        break
