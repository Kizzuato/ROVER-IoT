from smbus2 import SMBus
import time

bus = SMBus(1)
MPU_ADDR = 0x68  # MPU9250 / MPU6050
AK_ADDR = 0x0C   # Magnetometer

# Wake up MPU
bus.write_byte_data(MPU_ADDR, 0x6B, 0)

def read_word(addr, reg):
    high = bus.read_byte_data(addr, reg)
    low = bus.read_byte_data(addr, reg+1)
    val = (high << 8) + low
    if val >= 0x8000:
        val = -((65535 - val) + 1)
    return val

while True:
    acc_x = read_word(MPU_ADDR, 0x3B)
    acc_y = read_word(MPU_ADDR, 0x3D)
    acc_z = read_word(MPU_ADDR, 0x3F)

    gyro_x = read_word(MPU_ADDR, 0x43)
    gyro_y = read_word(MPU_ADDR, 0x45)
    gyro_z = read_word(MPU_ADDR, 0x47)

    print(f"Acc: {acc_x},{acc_y},{acc_z} | Gyro: {gyro_x},{gyro_y},{gyro_z}")
    time.sleep(0.5)
