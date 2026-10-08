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

# Guarda aquí el momento exacto en que empezamos.
t0 = time.time()

# Abre este ejecutable de Stockfish y establece la comunicación con él
# y el resultado guardamos en 'engine'
# chess.engine es un módulo de python-chess que proporciona
# una interfaz para interactuar con motores de ajedrez compatibles con UCI (Universal Chess Interface).
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
    # Guarda en result lo que devuelve el método play del objeto engine,
    # pasándole board y un límite de tiempo definido por THINK_TIME
    result = engine.play(board, chess.engine.Limit(time=THINK_TIME))
    # Devuelve la jugada almacenada en el atributo move del objeto result,
    # convertida a formato UCI mediante el método uci()
    return result.move.uci()


# =========================
# SHUTDOWN
# =========================

def shutdown_stockfish():
    # Intentá ejecutar el código que viene;
    # si ocurre un error, ignoralo.
    try:
        engine.quit()
    except:
        pass
