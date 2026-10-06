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
    return chess.Board()


def create_move(move_uci):
    return chess.Move.from_uci(move_uci)


# =========================
# HUMAN MOVE
# =========================

def validate_human_move(board, move_uci):

    move = chess.Move.from_uci(move_uci)

    if move not in board.legal_moves:
        return None

    return move


def push_move(board, move):
    board.push(move)


# =========================
# CAPTURE
# =========================

def is_capture(board, move):
    return board.is_capture(move)


def get_capture_squares(move):
    capture_square = chess.square_name(move.to_square)
    from_square = chess.square_name(move.from_square)

    return capture_square, from_square


# =========================
# GAME OVER
# =========================

def is_game_over(board):
    return board.is_game_over()


def get_result(board):
    return board.result()
