import argparse
import asyncio
import json
import os
import time

import websockets


DEFAULT_PI_IP = "100.69.90.121"
DEFAULT_PORT = 8765
DEFAULT_RATE_HZ = 20.0
DEFAULT_FORWARD_LIMIT = 0.30
DEFAULT_REVERSE_LIMIT = 0.20
DEFAULT_STEERING_LIMIT = 0.80
THROTTLE_STEP = 0.05
STEERING_STEP = 0.10


def clamp(value, lo, hi):
    return max(lo, min(hi, value))


class WindowsKeyReader:
    def __init__(self):
        if os.name != "nt":
            raise SystemExit("keyboard_send.py expects a Windows terminal.")
        import msvcrt

        self.msvcrt = msvcrt

    def read_key(self):
        if not self.msvcrt.kbhit():
            return None
        key = self.msvcrt.getwch()
        if key in ("\x00", "\xe0"):
            special = self.msvcrt.getwch()
            return {
                "H": "up",
                "P": "down",
                "K": "left",
                "M": "right",
            }.get(special)
        return key.lower()


def parse_args():
    parser = argparse.ArgumentParser(
        description="Drive the RC car over Tailscale using keyboard commands."
    )
    parser.add_argument("--host", default=DEFAULT_PI_IP, help="Pi Tailscale IP or DNS name.")
    parser.add_argument("--port", type=int, default=DEFAULT_PORT)
    parser.add_argument("--rate-hz", type=float, default=DEFAULT_RATE_HZ)
    parser.add_argument("--forward-limit", type=float, default=DEFAULT_FORWARD_LIMIT)
    parser.add_argument("--reverse-limit", type=float, default=DEFAULT_REVERSE_LIMIT)
    parser.add_argument("--steering-limit", type=float, default=DEFAULT_STEERING_LIMIT)
    return parser.parse_args()


def print_controls(args):
    print("Keyboard RC control")
    print(f"Connecting to ws://{args.host}:{args.port}")
    print()
    print("Controls:")
    print("  W or Up       increase forward throttle")
    print("  S or Down     increase reverse/brake throttle")
    print("  A or Left     steer left")
    print("  D or Right    steer right")
    print("  Space         neutral throttle")
    print("  C             center steering")
    print("  X             neutral throttle and center steering")
    print("  Q             quit")
    print()
    print(
        "Limits: "
        f"forward={args.forward_limit:.2f}, "
        f"reverse={args.reverse_limit:.2f}, "
        f"steering={args.steering_limit:.2f}"
    )
    print()


def apply_key(key, steering, throttle, args):
    if key in ("w", "up"):
        throttle = clamp(throttle + THROTTLE_STEP, -args.reverse_limit, args.forward_limit)
    elif key in ("s", "down"):
        throttle = clamp(throttle - THROTTLE_STEP, -args.reverse_limit, args.forward_limit)
    elif key in ("a", "left"):
        steering = clamp(steering - STEERING_STEP, -args.steering_limit, args.steering_limit)
    elif key in ("d", "right"):
        steering = clamp(steering + STEERING_STEP, -args.steering_limit, args.steering_limit)
    elif key == " ":
        throttle = 0.0
    elif key == "c":
        steering = 0.0
    elif key == "x":
        steering = 0.0
        throttle = 0.0
    return steering, throttle


async def send_loop(args):
    reader = WindowsKeyReader()
    uri = f"ws://{args.host}:{args.port}"
    steering = 0.0
    throttle = 0.0
    period_s = 1.0 / args.rate_hz
    last_print_s = 0.0

    print_controls(args)

    async with websockets.connect(uri) as ws:
        print("Connected. Starting at center steering and neutral throttle.")
        try:
            while True:
                key = reader.read_key()
                if key == "q":
                    break
                if key is not None:
                    steering, throttle = apply_key(key, steering, throttle, args)

                payload = {"steering": steering, "throttle": throttle}
                await ws.send(json.dumps(payload))

                now_s = time.monotonic()
                if key is not None or (now_s - last_print_s) >= 1.0:
                    print(f"steering={steering:+.2f} throttle={throttle:+.2f}")
                    last_print_s = now_s

                await asyncio.sleep(period_s)
        finally:
            payload = {"steering": 0.0, "throttle": 0.0}
            await ws.send(json.dumps(payload))
            print("Sent stop command. Exiting.")


def main():
    args = parse_args()
    if args.rate_hz <= 0:
        raise SystemExit("rate-hz must be greater than 0")
    if not 0.0 <= args.forward_limit <= 1.0:
        raise SystemExit("forward-limit must be between 0.0 and 1.0")
    if not 0.0 <= args.reverse_limit <= 1.0:
        raise SystemExit("reverse-limit must be between 0.0 and 1.0")
    if not 0.0 <= args.steering_limit <= 1.0:
        raise SystemExit("steering-limit must be between 0.0 and 1.0")

    asyncio.run(send_loop(args))


if __name__ == "__main__":
    main()
