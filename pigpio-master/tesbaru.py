#!/usr/bin/env python3
import time
import os

# =========================
# CONFIG
# =========================
PWM_CHIP = "/sys/class/pwm/pwmchip0"

RPWM_CH = 0      # GPIO18
LPWM_CH = 1      # GPIO19

R_EN_PIN = 23
L_EN_PIN = 24

PWM_FREQ = 20000          # 20 kHz
PERIOD_NS = int(1e9 / PWM_FREQ)
SPEED_PERCENT = 50        # 0 - 100

# =========================
# HELPER
# =========================
def write(path, value):
    with open(path, "w") as f:
        f.write(str(value))

def export_if_needed(path, export_path, idx):
    if not os.path.exists(path):
        write(export_path, idx)

# =========================
# SETUP GPIO
# =========================
export_if_needed(f"/sys/class/gpio/gpio{R_EN_PIN}", "/sys/class/gpio/export", R_EN_PIN)
export_if_needed(f"/sys/class/gpio/gpio{L_EN_PIN}", "/sys/class/gpio/export", L_EN_PIN)

write(f"/sys/class/gpio/gpio{R_EN_PIN}/direction", "out")
write(f"/sys/class/gpio/gpio{L_EN_PIN}/direction", "out")

# Enable driver
write(f"/sys/class/gpio/gpio{R_EN_PIN}/value", "1")
write(f"/sys/class/gpio/gpio{L_EN_PIN}/value", "1")

# =========================
# SETUP PWM
# =========================
export_if_needed(f"{PWM_CHIP}/pwm{RPWM_CH}", f"{PWM_CHIP}/export", RPWM_CH)
export_if_needed(f"{PWM_CHIP}/pwm{LPWM_CH}", f"{PWM_CHIP}/export", LPWM_CH)

time.sleep(0.1)

write(f"{PWM_CHIP}/pwm{RPWM_CH}/period", PERIOD_NS)
write(f"{PWM_CHIP}/pwm{LPWM_CH}/period", PERIOD_NS)

duty = int(SPEED_PERCENT / 100 * PERIOD_NS)

# MAJU (RPWM aktif)
write(f"{PWM_CHIP}/pwm{RPWM_CH}/duty_cycle", duty)
write(f"{PWM_CHIP}/pwm{LPWM_CH}/duty_cycle", 0)

write(f"{PWM_CHIP}/pwm{RPWM_CH}/enable", 1)
write(f"{PWM_CHIP}/pwm{LPWM_CH}/enable", 1)

print("Motor muter terus (50%). Ctrl+C untuk stop.")

try:
    while True:
        time.sleep(1)
except KeyboardInterrupt:
    print("\nStop motor")

finally:
    write(f"{PWM_CHIP}/pwm{RPWM_CH}/duty_cycle", 0)
    write(f"{PWM_CHIP}/pwm{LPWM_CH}/duty_cycle", 0)
    write(f"{PWM_CHIP}/pwm{RPWM_CH}/enable", 0)
    write(f"{PWM_CHIP}/pwm{LPWM_CH}/enable", 0)
    write(f"/sys/class/gpio/gpio{R_EN_PIN}/value", 0)
    write(f"/sys/class/gpio/gpio{L_EN_PIN}/value", 0)
    print("Selesai")
