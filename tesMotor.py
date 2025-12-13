import pigpio
pi = pigpio.pi()
pi.write(23,1)
pi.write(24,1)
while True:
    print("50%")
    pi.hardware_PWM(18,20000,500000)  # maju 50%
    pi.hardware_PWM(19,20000,0)
