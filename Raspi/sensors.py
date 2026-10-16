
# =======================================================================
#                  🔹 O N Y X - P R O 🔹
# =======================================================================
#  Archivo   : sensors.py
#  Autor     : Klaus Michalsky
#  Fecha     : Oct-2026
# -----------------------------------------------------------------------
#  ▫️ DESCRIPCIÓN
#     - Comunicación I2C con los MCP23017
#     - Lectura de la matriz de 64 sensores Hall
#     - Detección de ocupación de las casillas
#     - Detección de cambios en el tablero
#     - Gestión del botón de confirmación
# =======================================================================

from smbus2 import SMBus
from gpiozero import Button
import time


# ============================================================
# CONFIGURACIÓN I2C
# ============================================================

I2C_ID = 0
SDA_PIN = 16
SCL_PIN = 17
I2C_FREQ = 100000


# ============================================================
# MCP23017
# ============================================================
# Placa	Dirección I²C	A2	A1	A0
# 1	0x20	            0	0	0
# 2	0x21	            0	0	1
# 3	0x22	            0	1	0
# 4	0x23	            0	1	1

MCP_ADDRESSES = [0x20, 0x21, 0x22, 0x23]

IODIRA = 0x00
IODIRB = 0x01

GPIOA = 0x12
GPIOB = 0x13


# ============================================================
# BOTÓN DE CONFIRMACIÓN
# ============================================================

BUTTON_PIN = 18


# ============================================================
# MAPEO FÍSICO DEL TABLERO
# ============================================================

BOARD_SQUARES = [

    # --------------------------------------------------------
    # PLACA 1 -> 0x20
    # --------------------------------------------------------

    [
        "A1", "B1", "C1", "D1",
        "A2", "B2", "C2", "D2",
        "A3", "B3", "C3", "D3",
        "A4", "B4", "C4", "D4"
    ],

    # --------------------------------------------------------
    # PLACA 2 -> 0x21
    # --------------------------------------------------------

    [
        "E1", "F1", "G1", "H1",
        "E2", "F2", "G2", "H2",
        "E3", "F3", "G3", "H3",
        "E4", "F4", "G4", "H4"
    ],

    # --------------------------------------------------------
    # PLACA 3 -> 0x22
    # --------------------------------------------------------

    [
        "H8", "G8", "F8", "E8",
        "H7", "G7", "F7", "E7",
        "H6", "G6", "F6", "E6",
        "H5", "G5", "F5", "E5"
    ],

    # --------------------------------------------------------
    # PLACA 4 -> 0x23
    # --------------------------------------------------------

    [
        "D8", "C8", "B8", "A8",
        "D7", "C7", "B7", "A7",
        "D6", "C6", "B6", "A6",
        "D5", "C5", "B5", "A5"
    ]
]


# ============================================================
# ESTADO DEL TABLERO
# ============================================================

board_state = {
    square: False
    for board in BOARD_SQUARES
    for square in board
}

previous_state = {}


# ============================================================
# VARIABLES DEL MOVIMIENTO
# ============================================================

move_from = None
move_to = None

move_active = False

pending_empty = None

capture_square = None


# ============================================================
# ESTADO DEL HARDWARE
# ============================================================

i2c = None
mcps = []
button = None


# ============================================================
# CLASE MCP23017
# ============================================================


class MCP23017:
    def __init__(self, bus, address):
        self.bus = bus
        self.address = address

    def write_register(self, register, value):
        self.bus.write_byte_data(self.address, register, value)

    def read_register(self, register):
        return self.bus.read_byte_data(self.address, register)

    def setup_inputs(self):
        self.write_register(IODIRA, 0xFF)
        self.write_register(IODIRB, 0xFF)

    def read_gpio(self):
        gpio_a = self.read_register(GPIOA)
        gpio_b = self.read_register(GPIOB)
        return gpio_a, gpio_b


# ============================================================
# INICIALIZAR SENSORES
# ============================================================


def init_sensors():
    global i2c, mcps, button, previous_state

    # Abrir el bus I2C 1 de la Raspberry Pi
    i2c = SMBus(1)

    # Comprobar los cuatro MCP23017
    detected_addresses = []

    for address in MCP_ADDRESSES:
        try:
            i2c.read_byte(address)
            detected_addresses.append(address)
        except OSError:
            print(f"MCP23017 no detectado: 0x{address:02X}")

    print("MCP23017 detectados:", [f"0x{a:02X}" for a in detected_addresses])

    if len(detected_addresses) != len(MCP_ADDRESSES):
        i2c.close()
        i2c = None
        raise OSError("Falta uno o más MCP23017")

    # Inicializar las cuatro placas
    mcps = []

    for address in MCP_ADDRESSES:
        mcp = MCP23017(i2c, address)
        mcp.setup_inputs()
        mcps.append(mcp)

    # Leer el estado inicial del tablero
    read_all_sensors()
    previous_state = board_state.copy()

    # Inicializar botón de confirmación en GPIO 18
    button = Button(BUTTON_PIN, pull_up=True, bounce_time=0.05)

    print("ONYX-Pro: sensores inicializados")


# ============================================================
# LEER LOS 64 SENSORES
# ============================================================

def read_all_sensors():

    for board_index in range(4):

        value_a, value_b = mcps[board_index].read_gpio()
        squares = BOARD_SQUARES[board_index]

        # ----------------------------------------------------
        # GPIOA -> sensores 0-7
        # ----------------------------------------------------

        for bit in range(8):

            square = squares[bit]
            occupied = not bool(value_a & (1 << bit))

            board_state[square] = occupied

        # ----------------------------------------------------
        # GPIOB -> sensores 8-15
        # ----------------------------------------------------

        for bit in range(8):

            square = squares[bit + 8]
            occupied = not bool(value_b & (1 << bit))

            board_state[square] = occupied


# ============================================================
# DETECTAR CAMBIOS EN EL TABLERO
# ============================================================


def detect_changes():

    global previous_state

    # Leer el estado actual de los 64 sensores
    read_all_sensors()

    changes = []

    # Comparar el estado actual con el anterior
    for square in board_state:

        current = board_state[square]
        previous = previous_state.get(square, current)

        if current != previous:
            changes.append((square, current))

    # Guardar el estado actual para la próxima comparación
    previous_state = board_state.copy()

    return changes


# ============================================================
# MOSTRAR TABLERO
# ============================================================

def print_board():

    print()
    print("--------------- BOARD ----------------")

    for rank in range(8, 0, -1):

        line = str(rank) + " | "

        for file_index in range(8):

            file_letter = chr(ord("A") + file_index)
            square = file_letter + str(rank)

            if board_state[square]:
                line += "X "
            else:
                line += ". "

        print(line)

    print("    A B C D E F G H")
    print("---------------------------------------")
    print()


# ============================================================
# DEBUG BINARIO
# ============================================================

def byte_to_binary(value):

    result = ""

    for bit in range(7, -1, -1):

        if value & (1 << bit):
            result += "1"
        else:
            result += "0"

    return result


# ============================================================
# DEBUG DE LOS 64 SENSORES
# ============================================================

def debug_all_sensors():

    print()
    print("================================================")
    print("             DEBUG 64 SENSORES")
    print("================================================")

    for board_index in range(4):

        address = MCP_ADDRESSES[board_index]
        value_a, value_b = mcps[board_index].read_gpio()

        print()
        print("PLACA", board_index + 1, "->", hex(address))
        print("GPIOA =", byte_to_binary(value_a), " HEX =", hex(value_a))
        print("GPIOB =", byte_to_binary(value_b), " HEX =", hex(value_b))
        print()

        squares = BOARD_SQUARES[board_index]

        for i in range(16):

            if i < 8:
                occupied = not bool(value_a & (1 << i))
            else:
                occupied = not bool(value_b & (1 << (i - 8)))

            sensor_number = board_index * 16 + i

            print(
                "DRV",
                sensor_number,
                "->",
                squares[i],
                "->",
                "X" if occupied else "."
            )

    print()
    print("================================================")
    print()


# ============================================================
# DETECTAR BOTÓN
# ============================================================
# Esto funciona con gpiozero: devuelve True mientras el botón está pulsado
# y False cuando está suelto.
def button_pressed():
    if button is None:
        return False

    return button.is_pressed


# ============================================================
# ESPERAR LIBERACIÓN DEL BOTÓN
# ============================================================
# Así espera hasta que sueltes el botón. time.sleep(0.01) sustituye a time.sleep_ms(10),
# que no existe en Python normal de Linux sino en MicroPython.
# Esto es para no bloquear el hilo principal durante demasiado tiempo.
def wait_button_release():
    if button is None:
        return

    while button.is_pressed:
        time.sleep(0.01)
