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
import chess
import chess.engine

from config import STOCKFISH_PATH, THINK_TIME
from robot import (
    ser,
    reset_robot,
    send_to_robot,
    wait_done,
    do_homing,
    wait_any,
    shutdown_robot,
)

print("Reset RP2040...")
reset_robot()

# =========================
# STOCKFISH INIT
# =========================

print("Iniciando Stockfish...")
t0 = time.time()

engine = chess.engine.SimpleEngine.popen_uci(
    STOCKFISH_PATH,
    timeout=30.0
)

print("Stockfish OK")
print(f"Tiempo de inicio: {time.time() - t0:.2f} segundos")

board = chess.Board()

time.sleep(1)


# =========================
# STOCKFISH MOVE
# =========================


def get_best_move():
    result = engine.play(board, chess.engine.Limit(time=THINK_TIME))
    return result.move.uci()

# =========================
# SHUTDOWN
# =========================


def shutdown():
    try:
        engine.quit()
    except:
        pass

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
            human_move = chess.Move.from_uci(move)

            if human_move not in board.legal_moves:
                print("❌ Jugada ilegal")
                continue

        except ValueError:
            print("❌ Formato inválido")
            continue

        board.push(human_move)
        print("👤 Humano:", move)

        human_turn = False

    # =====================
    # TURNO ROBOT
    # =====================

    else:

        ser.reset_input_buffer()

        stockfish_move = get_best_move()
        move = chess.Move.from_uci(stockfish_move)

        print("🤖 Stockfish:", stockfish_move)

        # =====================
        # CAPTURA
        # =====================
        if board.is_capture(move):

            capture_square = chess.square_name(move.to_square)
            from_square = chess.square_name(move.from_square)

            send_to_robot(f"REMOVE {capture_square} {from_square}")

            # 🔥 SOLO esperar final real del sistema completo
            # o "CAPTURE DONE + FINAL DONE" mejor aún
            wait_any("MOVE DONE", "CAPTURE DONE")

            print("✅ Captura completada")

        else:
            send_to_robot(stockfish_move)
            wait_done()

        board.push(move)

        human_turn = True

    # =====================
    # FIN PARTIDA
    # =====================

    if board.is_game_over():
        print("\n🏁 Fin de partida")
        print(board.result())
        shutdown()
        break
