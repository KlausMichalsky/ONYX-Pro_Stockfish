# =======================================================================
#                         🔹 O N Y X - P R O 🔹
# =======================================================================
#  Archivo   : stockfish.py
#  Autor     : Klaus Michalsky
#  Fecha     : Oct-2026
# -----------------------------------------------------------------------
#  ▫️ DESCRIPCIÓN
#     - Inicialización de Stockfish
#     - Gestión del motor de ajedrez
#     - Cálculo de la mejor jugada
#     - Cierre del motor
# =======================================================================

import time
import chess
import chess.engine

from config import STOCKFISH_PATH, THINK_TIME


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


# =========================
# BEST MOVE
# =========================

def get_best_move(board):
    result = engine.play(
        board,
        chess.engine.Limit(time=THINK_TIME)
    )

    return result.move.uci()


# =========================
# SHUTDOWN
# =========================

def shutdown_stockfish():
    try:
        engine.quit()
    except:
        pass
