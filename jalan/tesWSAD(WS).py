import asyncio
import websockets
import pigpio
import time

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

# Enable driver
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
STEP_SIZE = 10       # naik/turun kecepatan tiap step
STEP_DELAY = 0.01    # 10 ms
lastUpdate = time.time()

# ============================
# MOTOR CONTROL FUNCTIONS
# ============================
def set_motor(speed):
    """speed -100..100"""
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

        # Kirim PWM ke drive motor
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
    spd = max(0, min(spd, 100))  # kita pakai 0..100% untuk smooth
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
# WEBSOCKET SERVER
# ============================
async def handler(ws):
    async for msg in ws:
        print(f"[WS RECEIVED] {msg}")
        try:
            stir, dir_str, spd_str = [x.strip() for x in msg.split(",")]
            spd = int(spd_str)
        except Exception as e:
            print(f"[ERROR] Invalid message: {msg} ({e})")
            continue

        handleSteering(stir)
        handleMotor(dir_str, spd)
        await ws.send("OK")

async def main():
    async with websockets.serve(handler, "0.0.0.0", 8000):
        print("WebSocket server running on ws://0.0.0.0:8000")
        while True:
            updateMotor()
            log_status()
            await asyncio.sleep(STEP_DELAY)

# ============================
# CLEANUP
# ============================
try:
    asyncio.run(main())
except KeyboardInterrupt:
    pass
finally:
    # Matikan semua pin & PWM
    for pin in [RPWM_PIN, LPWM_PIN, ENA, R_EN_PIN, L_EN_PIN, IN1, IN2]:
        pi.write(pin, 0)
        pi.hardware_PWM(pin, 0, 0)
    pi.stop()
    print("Selesai")
