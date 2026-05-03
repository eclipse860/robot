import argparse
import time

import busio
from board import SCL, SDA
from adafruit_pca9685 import PCA9685

PWM_PERIOD_MS = 20.0
DEFAULT_FREQUENCY_HZ = 50
DEFAULT_CHANNEL = 1
DEFAULT_NEUTRAL_MS = 1.50
DEFAULT_FORWARD_MS = 1.64
DEFAULT_REVERSE_MS = 1.35


def ms_to_duty(pulse_ms):
    return int((pulse_ms / PWM_PERIOD_MS) * 65535)


def set_pulse(channel, label, pulse_ms, hold_s):
    print(f"{label}: {pulse_ms:.2f} ms")
    channel.duty_cycle = ms_to_duty(pulse_ms)
    time.sleep(hold_s)


def parse_args():
    parser = argparse.ArgumentParser(
        description="Run a conservative first ESC motor test from the PCA9685."
    )
    parser.add_argument("--channel", type=int, default=DEFAULT_CHANNEL)
    parser.add_argument("--neutral-ms", type=float, default=DEFAULT_NEUTRAL_MS)
    parser.add_argument("--forward-ms", type=float, default=DEFAULT_FORWARD_MS)
    parser.add_argument("--reverse-ms", type=float, default=DEFAULT_REVERSE_MS)
    parser.add_argument(
        "--reverse",
        action="store_true",
        help="Send the reverse pulse instead of the forward pulse.",
    )
    parser.add_argument("--arm-s", type=float, default=3.0)
    parser.add_argument("--run-s", type=float, default=0.5)
    parser.add_argument("--settle-s", type=float, default=1.0)
    parser.add_argument(
        "--armed",
        action="store_true",
        help="Required safety acknowledgement before the motor test will run.",
    )
    return parser.parse_args()


def validate_args(args):
    if not args.armed:
        raise SystemExit(
            "Refusing to run motor test without --armed.\n"
            "Confirm the robot is lifted, motor area is clear, ESC red receiver "
            "wire is disconnected, signal/ground are connected, and bench power "
            "current is limited."
        )
    for name, pulse_ms in (
        ("neutral-ms", args.neutral_ms),
        ("forward-ms", args.forward_ms),
        ("reverse-ms", args.reverse_ms),
    ):
        if not 1.0 <= pulse_ms <= 2.0:
            raise SystemExit(f"{name} must be between 1.0 ms and 2.0 ms")
    if args.forward_ms <= args.neutral_ms:
        raise SystemExit("forward-ms must be greater than neutral-ms")
    if args.reverse_ms >= args.neutral_ms:
        raise SystemExit("reverse-ms must be less than neutral-ms")


def main():
    args = parse_args()
    validate_args(args)

    print("Initializing I2C and PCA9685")
    i2c = busio.I2C(SCL, SDA)
    pca = PCA9685(i2c)
    pca.frequency = DEFAULT_FREQUENCY_HZ
    esc = pca.channels[args.channel]

    print(
        f"ESC motor test on PCA9685 channel {args.channel} at "
        f"{DEFAULT_FREQUENCY_HZ} Hz"
    )
    print("Press Ctrl-C to stop and return to neutral.")

    try:
        set_pulse(esc, "Neutral / arm", args.neutral_ms, args.arm_s)
        if args.reverse:
            set_pulse(esc, "Small reverse", args.reverse_ms, args.run_s)
        else:
            set_pulse(esc, "Small forward", args.forward_ms, args.run_s)
        set_pulse(esc, "Neutral", args.neutral_ms, args.settle_s)
        print("Done")
    except KeyboardInterrupt:
        print("\nInterrupted; returning to neutral")
        esc.duty_cycle = ms_to_duty(args.neutral_ms)
        time.sleep(args.settle_s)
    finally:
        esc.duty_cycle = ms_to_duty(args.neutral_ms)
        time.sleep(0.5)
        pca.deinit()


if __name__ == "__main__":
    main()
