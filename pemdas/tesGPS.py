import serial
import pynmea2
import time

# Configure the serial port
# !! REPLACE WITH YOUR PORT NAME AND BAUD RATE !!
SERIAL_PORT = "/dev/ttyAMA0" # Example for Raspberry Pi 
BAUD_RATE = 9600             # Common baud rate for BN-880

def get_gps_data():
    try:
        # Open the serial port
        ser = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=1)
        print(f"Connected to {SERIAL_PORT} at {BAUD_RATE} baud.")
        
        while True:
            # Read a line from the serial port
            line = ser.readline().decode('utf-8', errors='ignore').strip()
            
            if line.startswith('$GP'):
                try:
                    # Parse the NMEA sentence
                    msg = pynmea2.parse(line)
                    
                    # Check if the message contains position data (e.g., GPGGA or GPRMC)
                    if hasattr(msg, 'latitude') and hasattr(msg, 'longitude'):
                        if msg.latitude != 0.0 and msg.longitude != 0.0:
                            print("-" * 20)
                            print(f"Timestamp: {msg.timestamp}")
                            print(f"Latitude: {msg.latitude} {msg.lat_dir}")
                            print(f"Longitude: {msg.longitude} {msg.lon_dir}")
                            # Other data available depending on the NMEA sentence type:
                            # print(f"Altitude: {msg.altitude} {msg.altitude_units}")
                            # print(f"Satellites: {msg.num_sats}") 
                            print("-" * 20)
                            time.sleep(1) # Wait a second before checking again

                except pynmea2.ParseError as e:
                    # Handle parsing errors (corrupted or incomplete data lines)
                    print(f"Parse error: {e}")
                
    except serial.SerialException as e:
        print(f"Error opening serial port: {e}")
        print("Please check the port name, wiring, and ensure the port is not in use by another program (like gpsd).")
    except KeyboardInterrupt:
        print("Exiting program.")
    finally:
        if 'ser' in locals() and ser.isOpen():
            ser.close()

if __name__ == "__main__":
    get_gps_data()
