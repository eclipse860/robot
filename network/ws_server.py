import asyncio
import json
import time

import busio
from adafruit_pca9685 import PCA9685
from board import SCL, SDA
import websockets

HOST = "0.0.0.0"
PORT = 8765

# --- Failsafe ---
FAILSAFE_TIMEOUT_S = 0.30
WATCHDOG_PERIOD_S = 0.05

# --- Steering servo config ---
STEERING_CH = 0
THROTTLE_CH = 1
PWM_FREQ = 50
LEFT_MS = 1.20
CENTER_MS = 1.50
RIGHT_MS = 1.80
THROTTLE_MIN_MS = 1.50
THROTTLE_MAX_MS = 2.00


def clamp(v, lo, hi):
    return max(lo, min(hi, v))


def ms_to_duty(ms: float) -> int:
    return int((ms / 20.0) * 65535)


def steering_ms_from_unit(x: float) -> float:
    """x in [-1.0, +1.0] -> pulse width ms."""
    x = clamp(x, -1.0, 1.0)
    if x >= 0:
        return CENTER_MS + x * (RIGHT_MS - CENTER_MS)
    return CENTER_MS + x * (CENTER_MS - LEFT_MS)


def throttle_ms_from_unit(x: float) -> float:
    """x in [0.0, 1.0] -> pulse width ms."""
    x = clamp(x, 0.0, 1.0)
    return THROTTLE_MIN_MS + x * (THROTTLE_MAX_MS - THROTTLE_MIN_MS)


# --- PCA9685 init ---
i2c = busio.I2C(SCL, SDA)
pca = PCA9685(i2c)
pca.frequency = PWM_FREQ
steering = pca.channels[STEERING_CH]
throttle = pca.channels[THROTTLE_CH]


def set_steering_unit(x: float):
    ms = steering_ms_from_unit(x)
    steering.duty_cycle = ms_to_duty(ms)


def set_throttle_unit(x: float):
    ms = throttle_ms_from_unit(x)
    throttle.duty_cycle = ms_to_duty(ms)


# start safe
set_steering_unit(0.0)
set_throttle_unit(0.0)


async def handler(websocket):
    peer = websocket.remote_address
    print(f"Client connected: {peer}")

    last_rx = time.monotonic()

    async def watchdog():
        nonlocal last_rx
        while True:
            await asyncio.sleep(WATCHDOG_PERIOD_S)
            if (time.monotonic() - last_rx) > FAILSAFE_TIMEOUT_S:
                set_steering_unit(0.0)
                set_throttle_unit(0.0)

    wd_task = asyncio.create_task(watchdog())

    try:
        async for message in websocket:
            try:
                data = json.loads(message)
                x = float(data.get("steering", 0.0))
                t = float(data.get("throttle", 0.0))

                set_steering_unit(x)
                set_throttle_unit(t)

                last_rx = time.monotonic()
                print(f"RX steering={x:.2f} throttle={t:.2f}")
            except Exception as e:
                # bad input -> do not refresh timer; center immediately
                set_steering_unit(0.0)
                set_throttle_unit(0.0)
                print(f"Bad input -> centered: {e}")
    finally:
        wd_task.cancel()
        set_steering_unit(0.0)
        set_throttle_unit(0.0)
        print(f"Client disconnected: {peer} -> centered")


async def main():
    print(f"WebSocket listening on {HOST}:{PORT}")
    async with websockets.serve(handler, HOST, PORT):
        await asyncio.Future()


if __name__ == "__main__":
    asyncio.run(main())
