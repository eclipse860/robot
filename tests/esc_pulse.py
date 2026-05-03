import argparse
import time

import busio
from board import SCL, SDA
from adafruit_pca9685 import PCA9685

PWM_PERIOD_MS = 20.0
DEFAULT_FREQUENCY_HZ = 50
DEFAULT_CHANNEL = 1
DEFAULT_PULSE_MS = 1.50


def ms_to_duty(pulse_ms):
    return int((pulse_ms / PWM_PERIOD_MS) * 65535)


def parse_args():
    parser = argparse.ArgumentParser(
        description="Interactively hold ESC PWM pulses for signal diagnostics."
    )
    parser.add_argument("--channel", type=int, default=DEFAULT_CHANNEL)
    parser.add_argument("--pulse-ms", type=float, default=DEFAULT_PULSE_MS)
    parser.add_argument(
        "--armed",
        action="store_true",
        help="Required safety acknowledgement before the pulse will be sent.",
    )
    return parser.parse_args()


def validate_args(args):
    if not args.armed:
        raise SystemExit(
            "Refusing to send ESC pulse without --armed.\n"
            "Confirm the robot is lifted, motor area is clear, ESC red receiver "
            "wire is disconnected, signal/ground are connected, and bench power "
            "current is limited."
        )
    if not 1.0 <= args.pulse_ms <= 2.0:
        raise SystemExit("pulse-ms must be between 1.0 ms and 2.0 ms")


def main():
    args = parse_args()
    validate_args(args)

    print("Initializing I2C and PCA9685")
    i2c = busio.I2C(SCL, SDA)
    pca = PCA9685(i2c)
    pca.frequency = DEFAULT_FREQUENCY_HZ
    esc = pca.channels[args.channel]

    print(
        f"Starting at {args.pulse_ms:.2f} ms on PCA9685 channel {args.channel} "
        f"at {DEFAULT_FREQUENCY_HZ} Hz"
    )
    print("Type a pulse width like 1.00, 1.50, or 2.00, then press Enter.")
    print("Press Ctrl-C to return to neutral and stop.")

    try:
        esc.duty_cycle = ms_to_duty(args.pulse_ms)
        while True:
            value = input("pulse-ms> ").strip()
            if not value:
                continue
            pulse_ms = float(value)
            if not 1.0 <= pulse_ms <= 2.0:
                print("pulse-ms must be between 1.0 ms and 2.0 ms")
                continue
            print(f"Holding {pulse_ms:.2f} ms")
            esc.duty_cycle = ms_to_duty(pulse_ms)
    except ValueError:
        print("\nInvalid pulse value; returning to neutral")
    except KeyboardInterrupt:
        print("\nInterrupted; returning to neutral")
    finally:
        esc.duty_cycle = ms_to_duty(DEFAULT_PULSE_MS)
        time.sleep(0.5)
        pca.deinit()


if __name__ == "__main__":
    main()
