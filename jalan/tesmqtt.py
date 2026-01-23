import asyncio
import pigpio
import time
import paho.mqtt.client as mqtt

# ============================
# PIGPIO SETUP
# ============================
pi = pigpio.pi()
if not pi.connected:
    exit("Tidak bisa connect ke pigpio daemon. Jalankan: sudo pigpiod")

# ----------------------------
# MOTOR DRIVE (BTS7960)
# ----------------------------
RPWM_PIN = 18
LPWM_PIN = 19
R_EN_PIN = 23
L_EN_PIN = 24
for pin in [RPWM_PIN, LPWM_PIN, R_EN_PIN, L_EN_PIN]:
    pi.set_mode(pin, pigpio.OUTPUT)

pi.write(R_EN_PIN, 1)
pi.write(L_EN_PIN, 1)

PWM_FREQ_DRIVE = 20000
MAX_DUTY = 1000000

# ----------------------------
# STEERING MOTOR (L298N)
# ----------------------------
IN1 = 5
IN2 = 6
ENA = 13
for pin in [IN1, IN2, ENA]:
    pi.set_mode(pin, pigpio.OUTPUT)
pi.write(ENA, 0)

STEER_PWM_FREQ = 1000
STEER_DUTY = int(0.7 * MAX_DUTY)

# ============================
# MOTOR STATE
# ============================
currentSpeed = 0
targetSpeed = 0
currentDir = "stop"
STEP_SIZE = 10
STEP_DELAY = 0.01
lastUpdate = time.time()

# ============================
# MOTOR CONTROL FUNCTIONS
# ============================
def set_motor(speed):
    if speed > 0:
        pi.hardware_PWM(RPWM_PIN, PWM_FREQ_DRIVE, int(speed/100*MAX_DUTY))
        pi.hardware_PWM(LPWM_PIN, PWM_FREQ_DRIVE, 0)
    elif speed < 0:
        pi.hardware_PWM(RPWM_PIN, PWM_FREQ_DRIVE, 0)
        pi.hardware_PWM(LPWM_PIN, PWM_FREQ_DRIVE, int(abs(speed)/100*MAX_DUTY))
    else:
        pi.hardware_PWM(RPWM_PIN, PWM_FREQ_DRIVE, 0)
        pi.hardware_PWM(LPWM_PIN, PWM_FREQ_DRIVE, 0)

def updateMotor():
    global currentSpeed, lastUpdate
    now = time.time()
    if now - lastUpdate >= STEP_DELAY:
        lastUpdate = now
        if currentSpeed < targetSpeed:
            currentSpeed += STEP_SIZE
        elif currentSpeed > targetSpeed:
            currentSpeed -= STEP_SIZE
        if abs(currentSpeed - targetSpeed) < STEP_SIZE:
            currentSpeed = targetSpeed
        set_motor(currentSpeed)

def handleSteering(stir):
    if stir.lower() == "kiri":
        pi.write(IN1, 1)
        pi.write(IN2, 0)
        pi.hardware_PWM(ENA, STEER_PWM_FREQ, STEER_DUTY)
    elif stir.lower() == "kanan":
        pi.write(IN1, 0)
        pi.write(IN2, 1)
        pi.hardware_PWM(ENA, STEER_PWM_FREQ, STEER_DUTY)
    else:
        pi.write(IN1, 0)
        pi.write(IN2, 0)
        pi.hardware_PWM(ENA, STEER_PWM_FREQ, 0)

def handleMotor(dir_str, spd):
    global targetSpeed, currentDir
    spd = max(0, min(spd, 100))
    if dir_str.lower() == "maju":
        targetSpeed = spd
        currentDir = "maju"
    elif dir_str.lower() == "mundur":
        targetSpeed = -spd
        currentDir = "mundur"
    else:
        targetSpeed = 0
        currentDir = "stop"

# ============================
# DEBUG LOGGING
# ============================
def log_status():
    duty_r = int(currentSpeed / 100 * MAX_DUTY if currentSpeed > 0 else 0)
    duty_l = int(abs(currentSpeed) / 100 * MAX_DUTY if currentSpeed < 0 else 0)
    steer_state = "CENTER"
    if pi.read(IN1) and not pi.read(IN2):
        steer_state = "LEFT"
    elif pi.read(IN2) and not pi.read(IN1):
        steer_state = "RIGHT"
    print(f"[DEBUG] DRIVE={currentDir} | PWM_R={duty_r} PWM_L={duty_l} | STEER={steer_state} | currentSpeed={currentSpeed} targetSpeed={targetSpeed}")

# ============================
# MQTT SETUP
# ============================
BROKER_URL  = "6ef2d03085bd433a947b703ea3f98f3e.s1.eu.hivemq.cloud"
BROKER_PORT = 8883
USERNAME    = "rover"
PASSWORD    = "roverRisbang2025"
TOPIC       = "robot/car1/control"


def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print("MQTT connected")
        client.subscribe(TOPIC)
    else:
        print(f"Failed to connect, return code {rc}")

def on_message(client, userdata, msg):
    try:
        stir, dir_str, spd_str = [x.strip() for x in msg.payload.decode().split(",")]
        spd = int(spd_str)
        handleSteering(stir)
        handleMotor(dir_str, spd)
        print(f"[MQTT RECEIVED] {msg.payload.decode()}")
    except Exception as e:
        print(f"[ERROR] Invalid MQTT message: {msg.payload.decode()} ({e})")

client = mqtt.Client()
client.username_pw_set(USERNAME, PASSWORD)
client.tls_set()  # karena pake port 8883
client.on_connect = on_connect
client.on_message = on_message
client.connect(BROKER_URL, BROKER_PORT, 60)
client.loop_start()

# ============================
# MAIN LOOP
# ============================
try:
    while True:
        updateMotor()
        log_status()
        time.sleep(STEP_DELAY)
except KeyboardInterrupt:
    pass
finally:
    for pin in [RPWM_PIN, LPWM_PIN, ENA, R_EN_PIN, L_EN_PIN, IN1, IN2]:
        pi.write(pin, 0)
        pi.hardware_PWM(pin, 0, 0)
    pi.stop()
    print("Selesai")
