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


def mirror_square(square):
    # square[0] Obtiene el primer carácter de la casilla
    # ord(square[0]) Obtiene el valor ASCII del primer carácter
    # ord("a") → 97, ord("e") → 101, ord("h") → 104
    # ord(square[0]) - ord("a") calcula cuántas posiciones hay desde la columna A. Para E, esto sería 4.
    # ord("h") - (ord(square[0]) - ord("a")) calcula la columna espejo. Para E, esto sería 104 - 4 = 100, que es la letra D.
    # chr(...) convierte el valor ASCII de vuelta a un carácter. Para 100, esto sería "d".
    file = chr(ord("h") - (ord(square[0]) - ord("a")))
    # similar para el rango, pero en lugar de usar valores ASCII,
    # usamos la posición numérica de la fila.
    rank = str(9 - int(square[1]))
    # devuelve la casilla espejo en formato UCI
    return file + rank


def mirror_move(move_uci):  # recibe una jugada en formato UCI
    # Dame los caracteres desde el principio hasta la posición 2, sin incluir la posición 2
    from_square = move_uci[:2]
    # caracteres desde el índice 2 hasta el 4, sin incluir el 4
    to_square = move_uci[2:4]
    promotion = move_uci[4:]  # caracteres desde el índice 4 hasta el final

    # aqui en el return de abajo la función mirror_square() se ejecuta dos veces:
    # devuelve la jugada espejo en formato UCI
    return mirror_square(from_square) + mirror_square(to_square) + promotion
