# =======================================================================
#                         🔹 O N Y X - P R O 🔹
# =======================================================================
#  Archivo   : game.py
#  Autor     : Klaus Michalsky
#  Fecha     : Oct-2026
# -----------------------------------------------------------------------
#  ▫️ DESCRIPCIÓN
#     - Gestión del tablero de ajedrez
#     - Validación de jugadas humanas
#     - Gestión de movimientos
#     - Detección de capturas
#     - Detección del final de partida
# =======================================================================

import chess


# =========================
# GAME INIT
# =========================

def create_board():
    return chess.Board()  # devuelve un objeto Board de la librería chess


def create_move(move_uci):
    # recibe una jugada en formato texto UCI
    # y la convierte en un objeto Move de python-chess
    return chess.Move.from_uci(move_uci)


# =========================
# HUMAN MOVE
# =========================

def validate_human_move(board, move_uci):
    # recibe un objeto Board y un string move_uci
    # y devuelve un objeto Move de la librería chess
    # si la jugada es legal,
    move = chess.Move.from_uci(move_uci)

    if move not in board.legal_moves:
        return None

    return move


def push_move(board, move):
    # recibe un objeto Board y un objeto Move
    # actualiza el estado del tablero
    board.push(move)


# =========================
# CAPTURE
# =========================

def is_capture(board, move):
    # recibe un objeto Board y un objeto Move
    # y devuelve True si la jugada es una captura,
    # False en caso contrario
    return board.is_capture(move)


def get_capture_squares(move):
    # Obtén las casillas de captura y de origen de move,
    # y guárdalas en capture_square y from_square
    capture_square = chess.square_name(move.to_square)
    from_square = chess.square_name(move.from_square)

    return capture_square, from_square


# =========================
# GAME OVER
# =========================

def is_game_over(board):
    # recibe un objeto Board
    # y devuelve True si la partida ha terminado,
    # False en caso contrario
    return board.is_game_over()


def get_result(board):
    # recibe un objeto Board
    # y devuelve el resultado de la partida en formato string
    return board.result()
