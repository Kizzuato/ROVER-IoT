import pigpio
import time

# ----------------------------
# Pin Definitions (PWM)
# ----------------------------
RPWM_PIN = 18   # PWM untuk maju
LPWM_PIN = 19   # PWM untuk mundur
# ----------------------------
# Enable pins (R_EN / L_EN) - sesuai wiring kamu
# jika ren dan len masih terhubung ke GPIO 23 dan 24
# maka set pin ini sebagai output dan aktifkan (HIGH)
# ----------------------------
R_EN_PIN = 23
L_EN_PIN = 24
# BTS7960 biasanya cuma butuh dua pin PWM + GND
# Pastikan GND Pi terhubung ke GND BTS

# ----------------------------
# Inisialisasi pigpio
# ----------------------------
pi = pigpio.pi()
if not pi.connected:
    exit("Tidak bisa connect ke pigpio daemon. Jalankan: sudo pigpiod")

PWM_FREQ = 20000  # 20 kHz
MAX_DUTY = 1000000  # pigpio duty cycle (0-1.000.000)

# Setup enable pins sebagai output dan nonaktifkan terlebih dahulu
pi.set_mode(R_EN_PIN, pigpio.OUTPUT)
pi.set_mode(L_EN_PIN, pigpio.OUTPUT)
pi.write(R_EN_PIN, 0)
pi.write(L_EN_PIN, 0)

def set_motor(speed):
    """
    speed: -100 hingga 100
    negatif = mundur, positif = maju
    """
    if speed > 0:
        duty = int(speed / 100 * MAX_DUTY)
        pi.hardware_PWM(RPWM_PIN, PWM_FREQ, duty)
        pi.hardware_PWM(LPWM_PIN, PWM_FREQ, 0)
    elif speed < 0:
        duty = int(abs(speed) / 100 * MAX_DUTY)
        pi.hardware_PWM(RPWM_PIN, PWM_FREQ, 0)
        pi.hardware_PWM(LPWM_PIN, PWM_FREQ, duty)
    else:
        pi.hardware_PWM(RPWM_PIN, PWM_FREQ, 0)
        pi.hardware_PWM(LPWM_PIN, PWM_FREQ, 0)

# ----------------------------
# Tes Motor - terus maju
# ----------------------------
try:
    print("Motor maju terus pada 50% - tekan Ctrl+C untuk berhenti")
    # Aktifkan R_EN/L_EN sesuai wiring (ren/len terhubung ke 23/24)
    pi.write(R_EN_PIN, 1)
    pi.write(L_EN_PIN, 1)
    set_motor(50)
    # Loop tak hingga agar motor terus maju. Gunakan Ctrl+C untuk berhenti.
    while True:
        time.sleep(1)
except KeyboardInterrupt:
    print("\nDiterima KeyboardInterrupt, berhenti...")
finally:
    # Hentikan PWM
    pi.hardware_PWM(RPWM_PIN, 0, 0)
    pi.hardware_PWM(LPWM_PIN, 0, 0)
    # Matikan enable pins
    try:
        pi.write(R_EN_PIN, 0)
        pi.write(L_EN_PIN, 0)
    except Exception:
        pass
    pi.stop()
    print("Selesai")
