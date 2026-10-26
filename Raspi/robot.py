# =======================================================================
#                         🔹 O N Y X - P R O 🔹
# =======================================================================
#  Archivo   : robot.py
#  Autor     : Klaus Michalsky
#  Fecha     : Oct-2026
# -----------------------------------------------------------------------
#  ▫️ DESCRIPCIÓN
#     - Comunicación con el RP2040
#     - Detección del puerto serie
#     - Envío y recepción de comandos
#     - Reset y homing del robot
# =======================================================================

import glob  # glob es un módulo de Python que permite buscar archivos
# o rutas que coincidan con un patrón. Es decir, para encontrar automáticamente el puerto donde Linux detectó el RP2040.
import time
import serial

from config import BAUDRATE, SERIAL_TIMEOUT


# =========================
# SERIAL INIT
# =========================

# Busca todos los puertos que empiecen por /dev/ttyACM
# y todos los que empiecen por /dev/ttyUSB, y guarda los resultados juntos en ports
# Busca automáticamente el puerto USB donde está conectado el RP2040
ports = glob.glob("/dev/ttyACM*") + glob.glob("/dev/ttyUSB*")

if not ports:
    raise Exception("No se encontró RP2040 conectado")

SERIAL_PORT = ports[0]

print("Usando puerto:", SERIAL_PORT)


print("🤖 Iniciando ONYX-Pro...")

# Abrime una conexión serie con este dispositivo
# y dame un objeto para poder comunicarme con él.
# Serial es una clase de la libreria pyserial
# que crea el objeto de conexión serie.
# serial.Serial es equivalente a: ☎️ "Llamá al RP2040."
# y guarda esa llamada en ser, que es un objeto de tipo Serial.
ser = serial.Serial(
    SERIAL_PORT,    # ← ¿a qué puerto?
    BAUDRATE,       # ← ¿a qué velocidad?
    timeout=SERIAL_TIMEOUT  # ← ¿cuánto esperar al leer?
)

time.sleep(2)


# =========================
# RESET ROBOT
# =========================

def reset_robot():
    ser.write(b"RESET\n")
    time.sleep(0.5)
    ser.reset_input_buffer()


# =========================
# SEND COMMAND
# =========================
def send_to_robot(cmd):
    ser.write((cmd + "\n").encode())  # encode() convierte el texto en bytes
# "e2e4\n"
#       ↓ encode()
# b"e2e4\n"
# ser.write() envía solo bytes al RP2040 a través del puerto serial.


# =========================
# INICIALIZAR ROBOT
# =========================
def initialize_robot():
    """Reinicia el RP2040 y prepara el contador de capturas."""

    print("Reset RP2040...")
    reset_robot()

    # Esperar a que el RP2040 esté listo.
    time.sleep(1)

    # Reiniciar el contador del Capture-Board.
    send_to_robot("CAPTURERESET")


# =========================
# WAIT DONE
# =========================
def wait_done():
    while True:
        # readline() devuelve bytes (Puerto serial)
        # decode() convierte bytes en str (texto)
        # strip() elimina espacios en blanco al inicio y al final de la cadena de texto.
        line = ser.readline().decode(errors="ignore").strip()

        if line:  # Si hemos recibido algo por Serial, haz lo siguiente
            print("RP2040:", line)

            if "DONE" in line:
                break


# =========================
# HOMING
# =========================

def do_homing():
    print("🤖 Enviando HOMING...")
    ser.write(b"HOMING\n")

    while True:
        line = ser.readline().decode(errors="ignore").strip()

        if line:
            print("RP2040:", line)

            if "DONE" in line:
                print("✅ HOMING COMPLETO")
                break


# =========================
# WAIT ANY
# =========================

def wait_any(*expected):  # Acepta una cantidad variable de argumentos
    while True:
        line = ser.readline().decode(errors="ignore").strip()

        if line:
            print("RP2040:", line)
            # for e in expected recorre uno por uno los mensajes que pasamos
            # if any ¿Hay al menos uno que sea verdadero?
            if any(e in line for e in expected):
                # return termina la función completa y vuelve al lugar desde donde fue llamada en main por ejemplo.
                # brake solo termina el bucle while, pero la función sigue ejecutándose.
                return


# =========================
# SHUTDOWN
# =========================

def shutdown_robot():
    try:
        if ser.is_open:
            ser.write(b"MOTOROFF\n")
            ser.flush()
            time.sleep(0.2)
    except Exception as e:
        print(f"⚠️ Error al apagar los motores: {e}")
    finally:
        try:
            if ser.is_open:
                ser.close()
        except Exception:
            pass


def execute_robot_move(robot_move, capture_square=None, from_square=None):
    if capture_square is not None and from_square is not None:
        send_to_robot(f"REMOVE {capture_square} {from_square}")
        wait_any("MOVE DONE", "CAPTURE DONE")
        print("✅ Captura completada")
    else:
        send_to_robot(robot_move)
        wait_done()
