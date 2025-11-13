from gpiozero import DigitalInputDevice
from signal import pause

sensor = DigitalInputDevice(17)

def hitung_pulse():
    print("Pulsa terdeteksi!")

sensor.when_activated = hitung_pulse

pause()