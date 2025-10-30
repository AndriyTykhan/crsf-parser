import serial
import time

# Connect to the virtual COM port
# On Windows: 'COM3', 'COM4', etc.
# On Linux: '/dev/ttyUSB0', '/dev/ttyACM0', etc.
ser = serial.Serial(
    port='COM4',  # Change to your port
    baudrate=115200,  # EdgeTX USB-VCP telemetry mirror baud rate
    timeout=1
)

# Read raw bytes
while True:
    if ser.in_waiting > 0:
        data = ser.read(ser.in_waiting)
        print(f"Received {len(data)} bytes: {data.hex()}")
    time.sleep(0.01)
