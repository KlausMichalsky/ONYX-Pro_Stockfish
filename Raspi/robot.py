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

import glob
import time
import serial

from config import BAUDRATE, SERIAL_TIMEOUT


# =========================
# SERIAL INIT
# =========================

ports = glob.glob("/dev/ttyACM*") + glob.glob("/dev/ttyUSB*")

if not ports:
    raise Exception("No se encontró RP2040 conectado")

SERIAL_PORT = ports[0]

print("Usando puerto:", SERIAL_PORT)


print("🤖 Iniciando ONYX-Pro...")

ser = serial.Serial(
    SERIAL_PORT,
    BAUDRATE,
    timeout=SERIAL_TIMEOUT
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
    ser.write((cmd + "\n").encode())


# =========================
# WAIT DONE
# =========================

def wait_done():
    while True:
        line = ser.readline().decode(errors="ignore").strip()

        if line:
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

def wait_any(*expected):
    while True:
        line = ser.readline().decode(errors="ignore").strip()

        if line:
            print("RP2040:", line)

            if any(e in line for e in expected):
                return


# =========================
# SHUTDOWN
# =========================

def shutdown_robot():
    try:
        ser.close()
    except:
        pass
