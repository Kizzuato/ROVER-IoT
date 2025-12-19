import serial
import time
import pynmea2

ser = serial.Serial('/dev/serial0', 9600, timeout=1)

time.sleep(2)  # beri waktu GPS stabil

while True:
    try:
        line = ser.readline().decode('ascii', errors='ignore').strip()
        if line.startswith('$GNGGA') or line.startswith('$GPGGA'):
            msg = pynmea2.parse(line)
            print("Latitude:", msg.latitude)
            print("Longitude:", msg.longitude)
            print("Altitude:", msg.altitude)
    except pynmea2.ParseError:
        continue
    except serial.SerialException as e:
        print("Serial error:", e)
        break
