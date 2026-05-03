import argparse
import time

import busio
from board import SCL, SDA
from adafruit_pca9685 import PCA9685

PWM_PERIOD_MS = 20.0
DEFAULT_FREQUENCY_HZ = 50
DEFAULT_CHANNEL = 1
DEFAULT_NEUTRAL_MS = 1.50
DEFAULT_FORWARD_MS = 2.00
DEFAULT_REVERSE_MS = 1.00


def ms_to_duty(pulse_ms):
    return int((pulse_ms / PWM_PERIOD_MS) * 65535)


def set_pulse(channel, label, pulse_ms):
    print(f"\nSending {label}: {pulse_ms:.2f} ms")
    channel.duty_cycle = ms_to_duty(pulse_ms)


def wait_for_user(prompt):
    input(f"{prompt}\nPress Enter here when done...")


def parse_args():
    parser = argparse.ArgumentParser(
        description="Guide QUICRUN WP 1080 G2 throttle range calibration."
    )
    parser.add_argument("--channel", type=int, default=DEFAULT_CHANNEL)
    parser.add_argument("--neutral-ms", type=float, default=DEFAULT_NEUTRAL_MS)
    parser.add_argument("--forward-ms", type=float, default=DEFAULT_FORWARD_MS)
    parser.add_argument("--reverse-ms", type=float, default=DEFAULT_REVERSE_MS)
    parser.add_argument(
        "--armed",
        action="store_true",
        help="Required safety acknowledgement before calibration will run.",
    )
    return parser.parse_args()


def validate_args(args):
    if not args.armed:
        raise SystemExit(
            "Refusing to run ESC calibration without --armed.\n"
            "Confirm the robot is lifted, motor area is clear, ESC red receiver "
            "wire is disconnected, ESC signal/ground are connected to PCA9685 "
            "channel 1, and bench power current is limited."
        )
    for name, pulse_ms in (
        ("neutral-ms", args.neutral_ms),
        ("forward-ms", args.forward_ms),
        ("reverse-ms", args.reverse_ms),
    ):
        if not 1.0 <= pulse_ms <= 2.0:
            raise SystemExit(f"{name} must be between 1.0 ms and 2.0 ms")


def main():
    args = parse_args()
    validate_args(args)

    print("Initializing I2C and PCA9685")
    i2c = busio.I2C(SCL, SDA)
    pca = PCA9685(i2c)
    pca.frequency = DEFAULT_FREQUENCY_HZ
    esc = pca.channels[args.channel]

    print(
        f"ESC calibration on PCA9685 channel {args.channel} at "
        f"{DEFAULT_FREQUENCY_HZ} Hz"
    )

    try:
        set_pulse(esc, "neutral", args.neutral_ms)
        wait_for_user(
            "1. Leave this script running.\n"
            "2. With ESC off, hold the ESC SET button.\n"
            "3. Press ESC ON/OFF.\n"
            "4. Release SET as soon as the red LED flashes."
        )

        wait_for_user(
            "Neutral is still being sent. Press the ESC SET button once now. "
            "The ESC should acknowledge neutral."
        )

        set_pulse(esc, "full forward", args.forward_ms)
        wait_for_user(
            "Press the ESC SET button once now. The ESC should acknowledge "
            "full forward."
        )

        set_pulse(esc, "full brake/reverse", args.reverse_ms)
        wait_for_user(
            "Press the ESC SET button once now. The ESC should acknowledge "
            "full brake/reverse."
        )

        set_pulse(esc, "neutral", args.neutral_ms)
        print("\nCalibration pulses complete. Wait at least 3 seconds before testing.")
        time.sleep(3.0)
    except KeyboardInterrupt:
        print("\nInterrupted; returning to neutral")
        esc.duty_cycle = ms_to_duty(args.neutral_ms)
        time.sleep(1.0)
    finally:
        esc.duty_cycle = ms_to_duty(args.neutral_ms)
        time.sleep(0.5)
        pca.deinit()


if __name__ == "__main__":
    main()
