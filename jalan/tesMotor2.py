import pigpio
import time

# ----------------------------
# Pin Definitions
# ----------------------------
ENA = 13  # PWM hardware
IN1 = 5
IN2 = 6

# ----------------------------
# Inisialisasi pigpio
# ----------------------------
pi = pigpio.pi()
if not pi.connected:
    exit("Tidak bisa connect ke pigpio daemon. Jalankan: sudo pigpiod")

PWM_FREQ = 1000     # 1 kHz
MAX_DUTY = 1000000  # pigpio duty cycle max

# Setup pin sebagai output
pi.set_mode(ENA, pigpio.OUTPUT)
pi.set_mode(IN1, pigpio.OUTPUT)
pi.set_mode(IN2, pigpio.OUTPUT)

# Matikan motor di awal
pi.write(IN1, 0)
pi.write(IN2, 0)
pi.hardware_PWM(ENA, PWM_FREQ, 0)

# ----------------------------
# Fungsi kendali motor
# ----------------------------
def set_motor(speed):
    """
    speed: -100 hingga 100
    negatif = mundur, positif = maju
    """
    duty = int(abs(speed)/100 * MAX_DUTY)
    if speed > 0:
        pi.write(IN1, 1)
        pi.write(IN2, 0)
        pi.hardware_PWM(ENA, PWM_FREQ, duty)
    elif speed < 0:
        pi.write(IN1, 0)
        pi.write(IN2, 1)
        pi.hardware_PWM(ENA, PWM_FREQ, duty)
    else:
        pi.write(IN1, 0)
        pi.write(IN2, 0)
        pi.hardware_PWM(ENA, PWM_FREQ, 0)

# ----------------------------
# Tes motor
# ----------------------------
try:
    print("Motor maju 50%")
    set_motor(50)
    time.sleep(30)

    print("Motor mundur 50%")
    set_motor(-50)
    time.sleep(3)

    print("Motor stop")
    set_motor(0)
except KeyboardInterrupt:
    print("\nKeyboardInterrupt, berhenti...")
finally:
    # Hentikan motor
    set_motor(0)
    pi.stop()
    print("Selesai")
