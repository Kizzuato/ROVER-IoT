import serial
import pynmea2
import time

# Sesuaikan dengan port serial yang Anda gunakan (ttyS0 untuk UART bawaan)
ser = serial.Serial('/dev/ttyS0', 9600, timeout=1) # 9600 baud rate, sesuaikan jika perlu

print("Membaca data GPS...")
while True:
    try:
        line = ser.readline().decode('ascii', errors='ignore').strip()
        if line.startswith('$GPGGA') or line.startswith('$GPRMC'):
            msg = pynmea2.parse(line)
            if hasattr(msg, 'latitude') and hasattr(msg, 'longitude'):
                print(f"Latitude: {msg.latitude}, Longitude: {msg.longitude}")
                print(f"Altitude: {msg.altitude} {msg.altitude_units}")
            # Tambahkan logika untuk data kompas (I2C) jika ada
        time.sleep(0.1)
    except Exception as e:
        print(f"Error: {e}")
        time.sleep(1)
