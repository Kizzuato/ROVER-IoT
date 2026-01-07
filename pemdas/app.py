from flask import Flask, jsonify, render_template, Response
import serial
import pynmea2
from smbus2 import SMBus
import threading
import time
import RPi.GPIO as GPIO
import atexit
import cv2

app = Flask(__name__)

# ===================== GPS =====================
gps_port = '/dev/serial0'
gps_baud = 9600
# gps_data = {"lat": None, "lon": None, "alt": None}
gps_data = {"lat": 11, "lon": 16, "alt": 41}

def read_gps():
    global gps_data
    try:
        ser = serial.Serial(gps_port, gps_baud, timeout=1)
        time.sleep(2)
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

# ===================== IMU (MPU6050) =====================
bus = SMBus(1)
MPU_ADDR = 0x68

try:
    bus.write_byte_data(MPU_ADDR, 0x6B, 0x00)
except Exception as e:
    print("MPU init error:", e)

INT_PIN = 4
GPIO.setmode(GPIO.BCM)
GPIO.setup(INT_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)

imu_data = {
    "acc": [0, 0, 0],
    "gyro": [0, 0, 0],
    "mag": [0, 0, 0],
    "heading": 0
}

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
            ax = read_word(MPU_ADDR, 0x3B)
            ay = read_word(MPU_ADDR, 0x3D)
            az = read_word(MPU_ADDR, 0x3F)

            gx = read_word(MPU_ADDR, 0x43)
            gy = read_word(MPU_ADDR, 0x45)
            gz = read_word(MPU_ADDR, 0x47)

            imu_data['acc'] = [ax, ay, az]
            imu_data['gyro'] = [gx, gy, gz]

            time.sleep(0.05)
        except Exception as e:
            print("IMU read error:", e)
            time.sleep(0.1)

# ===================== CAMERA =====================
camera = cv2.VideoCapture(1)
camera.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
camera.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

if not camera.isOpened():
    print("WARNING: Kamera tidak bisa dibuka")

def generate_frames():
    while True:
        success, frame = camera.read()
        if not success:
            time.sleep(0.1)
            continue

        ret, buffer = cv2.imencode('.jpg', frame)
        frame = buffer.tobytes()

        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')

# ===================== ROUTES =====================
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/data')
def data():
    return jsonify({
        "gps": gps_data,
        "imu": imu_data
    })

@app.route('/video')
def video():
    return Response(generate_frames(),
                    mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/snapshot')
def snapshot():
    ret, frame = camera.read()
    _, jpeg = cv2.imencode('.jpg', frame)
    return Response(jpeg.tobytes(), mimetype='image/jpeg')


# ===================== CLEANUP =====================
def cleanup():
    GPIO.cleanup()
    camera.release()

atexit.register(cleanup)

# ===================== MAIN =====================
if __name__ == '__main__':
    threading.Thread(target=read_gps, daemon=True).start()
    threading.Thread(target=read_imu_polling, daemon=True).start()
    app.run(host='0.0.0.0', port=5000, debug=False)
