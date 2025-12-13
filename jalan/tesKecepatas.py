import RPi.GPIO as gp
from time import sleep

SENSOR_PIN = 17
gp.setmode(gp.BCM)
gp.setup(SENSOR_PIN, gp.IN, pull_up_down=gp.PUD_UP)
pulse_count = 0

def hitung_pulse(channel):
    global pulse_count
    pulse_count += 1
    
gp.add_event_detect(SENSOR_PIN, gp.FALLING, callback=hitung_pulse)

try:
    while True:
        pulse_count = 0
        sleep(1)
        rpm = pulse_count * 60 
        print("Pulse count:", pulse_count)
        sleep(1)
        print(f"Kecepatan: {pulse_count} pulse per detik")
except KeyboardInterrupt:
    gp.cleanup()
    