# =======================================================================
#                     🔹 O N Y X - P R O 🔹
# =======================================================================
# Archivo : controller.py
# Descripción:
#     - Coordinación de los turnos de la partida.
#     - Gestión del turno humano.
# =======================================================================

import sensors

from game import (
    process_human_move,
    push_move,
    mirror_move,
)


# =========================
# TURNO HUMANO
# =========================

def run_human_turn(
    board,
    confirmed_state,
    change_history,
    mirror_coordinates,
):
    """Gestiona el turno humano y devuelve el estado confirmado."""

    print("\n♟️ Mové tus piezas y pulsá el botón para confirmar.")
    print("Podés corregir tus movimientos antes de confirmar.")

    while True:

        # Esperar el botón y obtener el estado del tablero.
        current_state = sensors.wait_for_human_confirmation(
            confirmed_state,
            change_history,
        )

        # Si el tablero volvió a la posición confirmada.
        if current_state is None:
            print("↩️ Tablero restaurado. Podés volver a mover.")
            continue

        try:
            # Identificar y validar la jugada humana.
            logical_move, human_move = process_human_move(
                board,
                confirmed_state,
                current_state,
                change_history,
                mirror_coordinates,
            )

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

        # Actualizar la posición confirmada.
        confirmed_state = current_state.copy()
        change_history.clear()

        return confirmed_state
