import pygame
import asyncio
import websockets
import sys

# === CONFIGURATION ===
# Replace with your ESP32 IP
ESP32_IP = "192.168.1.32" 
WS_URL = f"ws://{ESP32_IP}:81"

# Axis mappings (Default for G29 on Linux, might vary)
AXIS_STEERING = 0  # Left/Right
AXIS_GAS = 2       # Gas Pedal (0.0 to 1.0 or -1.0 to 1.0)
AXIS_BRAKE = 3     # Brake Pedal

# Deadzones and Sensitivity
STEERING_THRESHOLD = 0.3
GAS_THRESHOLD = -0.5 # Pygame usually maps pedals from -1 (idle) to 1 (pressed)

async def control_bridge():
    pygame.init()
    pygame.joystick.init()

    if pygame.joystick.get_count() == 0:
        print("No steering wheel/joystick detected!")
        return

    wheel = pygame.joystick.Joystick(0)
    wheel.init()
    print(f"Connected to: {wheel.get_name()}")

    async with websockets.connect(WS_URL) as ws:
        print(f"Connected to ESP32 at {WS_URL}")
        last_cmd = 'x'

        try:
            running = True
            while running:
                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        running = False

                # Read Inputs
                steering = wheel.get_axis(AXIS_STEERING)
                gas = wheel.get_axis(AXIS_GAS)
                brake = wheel.get_axis(AXIS_BRAKE)

                cmd = 'x' # Default Stop

                # Priority logic: Gas = Maju, Brake = Mundur
                if gas > GAS_THRESHOLD:
                    if steering < -STEERING_THRESHOLD:
                        cmd = 'a' # Kiri
                    elif steering > STEERING_THRESHOLD:
                        cmd = 'd' # Kanan
                    else:
                        cmd = 'w' # Maju
                elif brake > GAS_THRESHOLD:
                    cmd = 's' # Mundur
                elif abs(steering) > STEERING_THRESHOLD:
                    # If just turning without gas, maybe some low speed move?
                    # For now, let's keep it simple: steering only works with gas
                    # or just send 'a'/'d' and let ESP32 handle it.
                    if steering < -STEERING_THRESHOLD:
                        cmd = 'a'
                    else:
                        cmd = 'd'

                # Send command only if it changed to avoid flooding
                if cmd != last_cmd:
                    await ws.send(cmd)
                    print(f"Sent command: {cmd}")
                    last_cmd = cmd

                await asyncio.sleep(0.05) # 20Hz update rate

        except websockets.exceptions.ConnectionClosed:
            print("Connection to ESP32 closed.")
        except KeyboardInterrupt:
            print("Stopping bridge...")
        finally:
            await ws.send('x') # Emergency stop
            pygame.quit()

if __name__ == "__main__":
    if len(sys.argv) > 1:
        ESP32_IP = sys.argv[1]
        WS_URL = f"ws://{ESP32_IP}:81"
    
    print("Logitech RC Bridge")
    print("Usage: python3 logitech_bridge.py [ESP32_IP]")
    print(f"Trying to connect to {ESP32_IP}...")
    
    try:
        asyncio.run(control_bridge())
    except Exception as e:
        print(f"Error: {e}")
        print("\nMake sure you have installed: pip install pygame websockets")
