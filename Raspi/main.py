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
    initialize_robot,
    initialize_serial,
)

from stockfish import (
    initialize_stockfish,
    shutdown_stockfish,
)

from game import (
    create_board,
    is_game_over,
    get_result,
    sensor_occupancy_from_board,
)

from controller import run_game_loop

initialize_serial()

initialize_stockfish()

initialize_robot()

board = create_board()


# =========================
# SHUTDOWN
# =========================

def shutdown():
    """Cierra sensores, Stockfish y robot aunque falle una etapa."""

    shutdown_steps = (
        ("sensores", sensors.shutdown_sensors),
        ("Stockfish", shutdown_stockfish),
        ("robot", shutdown_robot),
    )

    for name, close_function in shutdown_steps:
        try:
            close_function()
        except Exception as error:
            print(f"⚠️ Error al cerrar {name}: {error}")


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

run_game_loop(
    board,
    human_turn,
    mirror_coordinates,
    confirmed_state,
    change_history,
)

# =========================
# FIN PARTIDA
# =========================

if is_game_over(board):
    print("\n🏁 Fin de partida")
    print(get_result(board))

    shutdown()
