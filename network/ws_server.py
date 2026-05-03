import asyncio
import json
import time

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
THROTTLE_REVERSE_MS = 1.00
THROTTLE_NEUTRAL_MS = 1.50
THROTTLE_FORWARD_MS = 2.00


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
    """x in [-1.0, +1.0] -> pulse width ms."""
    x = clamp(x, -1.0, 1.0)
    if x >= 0:
        return THROTTLE_NEUTRAL_MS + x * (THROTTLE_FORWARD_MS - THROTTLE_NEUTRAL_MS)
    return THROTTLE_NEUTRAL_MS + x * (THROTTLE_NEUTRAL_MS - THROTTLE_REVERSE_MS)


class RobotOutputs:
    def __init__(self, steering_channel, throttle_channel):
        self.steering_channel = steering_channel
        self.throttle_channel = throttle_channel

    def set_steering_unit(self, x: float):
        ms = steering_ms_from_unit(x)
        self.steering_channel.duty_cycle = ms_to_duty(ms)

    def set_throttle_unit(self, x: float):
        ms = throttle_ms_from_unit(x)
        self.throttle_channel.duty_cycle = ms_to_duty(ms)

    def set_safe(self):
        self.set_steering_unit(0.0)
        self.set_throttle_unit(0.0)


def create_outputs() -> RobotOutputs:
    # Pi-only imports stay here so this module can be imported on dev machines.
    import busio
    from adafruit_pca9685 import PCA9685
    from board import SCL, SDA

    i2c = busio.I2C(SCL, SDA)
    pca = PCA9685(i2c)
    pca.frequency = PWM_FREQ
    return RobotOutputs(pca.channels[STEERING_CH], pca.channels[THROTTLE_CH])


def apply_message(outputs: RobotOutputs, message: str):
    data = json.loads(message)
    x = float(data.get("steering", 0.0))
    t = float(data.get("throttle", 0.0))

    outputs.set_steering_unit(x)
    outputs.set_throttle_unit(t)
    return x, t


async def handler(websocket, outputs: RobotOutputs):
    peer = websocket.remote_address
    print(f"Client connected: {peer}")

    last_rx = time.monotonic()

    async def watchdog():
        nonlocal last_rx
        while True:
            await asyncio.sleep(WATCHDOG_PERIOD_S)
            if (time.monotonic() - last_rx) > FAILSAFE_TIMEOUT_S:
                outputs.set_safe()

    wd_task = asyncio.create_task(watchdog())

    try:
        async for message in websocket:
            try:
                x, t = apply_message(outputs, message)

                last_rx = time.monotonic()
                print(f"RX steering={x:.2f} throttle={t:.2f}")
            except Exception as e:
                # bad input -> do not refresh timer; center immediately
                outputs.set_safe()
                print(f"Bad input -> centered: {e}")
    finally:
        wd_task.cancel()
        outputs.set_safe()
        print(f"Client disconnected: {peer} -> centered")


async def main():
    outputs = create_outputs()
    outputs.set_safe()
    print(f"WebSocket listening on {HOST}:{PORT}")
    async with websockets.serve(lambda websocket: handler(websocket, outputs), HOST, PORT):
        await asyncio.Future()


if __name__ == "__main__":
    asyncio.run(main())
