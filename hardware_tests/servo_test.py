import argparse
import time

import busio
from adafruit_pca9685 import PCA9685
from board import SCL, SDA

PWM_PERIOD_MS = 20.0
DEFAULT_FREQUENCY_HZ = 50
DEFAULT_CHANNEL = 0
DEFAULT_LEFT_MS = 1.20
DEFAULT_CENTER_MS = 1.50
DEFAULT_RIGHT_MS = 1.80


def ms_to_duty(pulse_ms):
    return int((pulse_ms / PWM_PERIOD_MS) * 65535)


def set_pulse(channel, label, pulse_ms, hold_s):
    print(f"{label}: {pulse_ms:.2f} ms")
    channel.duty_cycle = ms_to_duty(pulse_ms)
    time.sleep(hold_s)


def parse_args():
    parser = argparse.ArgumentParser(
        description="Sweep a servo connected to the PCA9685 from the Raspberry Pi."
    )
    parser.add_argument("--channel", type=int, default=DEFAULT_CHANNEL)
    parser.add_argument("--left-ms", type=float, default=DEFAULT_LEFT_MS)
    parser.add_argument("--center-ms", type=float, default=DEFAULT_CENTER_MS)
    parser.add_argument("--right-ms", type=float, default=DEFAULT_RIGHT_MS)
    parser.add_argument("--hold-s", type=float, default=1.0)
    parser.add_argument("--cycles", type=int, default=5)
    parser.add_argument("--forever", action="store_true")
    return parser.parse_args()


def main():
    args = parse_args()

    print("Initializing I2C and PCA9685")
    i2c = busio.I2C(SCL, SDA)
    pca = PCA9685(i2c)
    pca.frequency = DEFAULT_FREQUENCY_HZ
    servo = pca.channels[args.channel]

    print(
        f"Servo test on PCA9685 channel {args.channel} at "
        f"{DEFAULT_FREQUENCY_HZ} Hz"
    )
    print("Press Ctrl-C to stop and recenter.")

    try:
        cycle = 0
        while args.forever or cycle < args.cycles:
            cycle += 1
            print(f"Cycle {cycle}")
            set_pulse(servo, "Center", args.center_ms, args.hold_s)
            set_pulse(servo, "Left", args.left_ms, args.hold_s)
            set_pulse(servo, "Center", args.center_ms, args.hold_s)
            set_pulse(servo, "Right", args.right_ms, args.hold_s)

        print("Done; recentering")
        servo.duty_cycle = ms_to_duty(args.center_ms)
    except KeyboardInterrupt:
        print("\nInterrupted; recentering")
        servo.duty_cycle = ms_to_duty(args.center_ms)
    finally:
        time.sleep(0.5)
        pca.deinit()


if __name__ == "__main__":
    main()
