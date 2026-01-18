from board import SCL, SDA
import busio
import time
from adafruit_pca9685 import PCA9685

# Initialize I2C
i2c = busio.I2C(SCL, SDA)

# Initialize PCA9685
pca = PCA9685(i2c)
pca.frequency = 50  # Standard servo frequency

def ms_to_duty(ms):
    """Convert milliseconds to PCA9685 duty cycle"""
    return int((ms / 20.0) * 65535)

# Steering servo on Channel 0
servo = pca.channels[0]

print("Servo test starting")

while True:
    print("Center")
    servo.duty_cycle = ms_to_duty(1.50)
    time.sleep(2)

    print("Left")
    servo.duty_cycle = ms_to_duty(1.20)
    time.sleep(2)

    print("Right")
    servo.duty_cycle = ms_to_duty(1.80)
    time.sleep(2)

