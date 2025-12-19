from flask import Flask, jsonify, render_template
import serial
import pynmea2
from smbus2 import SMBus
import threading
import time
import RPi.GPIO as GPIO
import atexit

app = Flask(__name__)

# ---------------- GPS ----------------
gps_port = '/dev/serial0'
gps_baud = 9600
gps_data = {"lat": None, "lon": None, "alt": None}

def read_gps():
    global gps_data
    try:
        ser = serial.Serial(gps_port, gps_baud, timeout=1)
        time.sleep(2)  # beri waktu GPS stabil
        while True:
            line = ser.readline().decode('ascii', errors='ignore').strip()
            if line.startswith('$GNGGA') or line.startswith('$GPGGA'):
                try:
                    msg = pynmea2.parse(line)
                    gps_data['lat'] = msg.latitude
                    gps_data['lon'] = msg.longitude
                    gps_data['alt'] = msg.altitude
                except pynmea2.ParseError:
                    continue
    except Exception as e:
        print("GPS error:", e)

# ---------------- IMU ----------------
bus = SMBus(1)
MPU_ADDR = 0x68

# Wake up MPU6050
bus.write_byte_data(MPU_ADDR, 0x6B, 0x00)

# Setup GPIO INT (untuk nanti optional)
INT_PIN = 4
GPIO.setmode(GPIO.BCM)
GPIO.setup(INT_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)

imu_data = {"acc": [0, 0, 0], "gyro": [0, 0, 0], "mag": [0, 0, 0], "heading": 0}

def read_word(addr, reg):
    high = bus.read_byte_data(addr, reg)
    low = bus.read_byte_data(addr, reg + 1)
    val = (high << 8) + low
    if val >= 0x8000:
        val = -((65535 - val) + 1)
    return val

def read_imu_polling():
    global imu_data
    while True:
        try:
            # Baca Accelerometer
            ax = read_word(MPU_ADDR, 0x3B)
            ay = read_word(MPU_ADDR, 0x3D)
            az = read_word(MPU_ADDR, 0x3F)
            imu_data['acc'] = [ax, ay, az]

            # Baca Gyroscope
            gx = read_word(MPU_ADDR, 0x43)
            gy = read_word(MPU_ADDR, 0x45)
            gz = read_word(MPU_ADDR, 0x47)
            imu_data['gyro'] = [gx, gy, gz]

            # Magnetometer & heading sementara
            imu_data['mag'] = [0, 0, 0]
            imu_data['heading'] = 0

            # Cek pin INT (opsional, tetap bisa pakai)
            if GPIO.input(INT_PIN) == 0:
                # bisa panggil callback jika mau
                pass

            time.sleep(0.05)  # 20Hz update rate
        except Exception as e:
            print("IMU read error:", e)
            time.sleep(0.1)

# ---------------- Flask routes ----------------
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/data')
def data():
    return jsonify({"gps": gps_data, "imu": imu_data})

# ---------------- Cleanup ----------------
atexit.register(GPIO.cleanup)

# ---------------- Main ----------------
if __name__ == '__main__':
    # Start GPS thread
    threading.Thread(target=read_gps, daemon=True).start()
    # Start IMU polling thread
    threading.Thread(target=read_imu_polling, daemon=True).start()
    # Run Flask server
    app.run(host='0.0.0.0', port=5000)
