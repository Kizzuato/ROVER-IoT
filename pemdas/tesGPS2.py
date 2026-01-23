import gpsd
import time

# Connect to the local gpsd daemon
gpsd.connect()

while True:
    # Get the current GPS data
    packet = gpsd.get_current()
    
    if packet.mode >= 2: # Mode 2 means a 2D fix, Mode 3 means a 3D fix
        print(f"Latitude: {packet.lat}")
        print(f"Longitude: {packet.lon}")
        # print(f"Speed: {packet.hspeed} m/s")
        # print(f"Time: {packet.time}")
    else:
        print("Waiting for a GPS fix...")
        
    time.sleep(1)
