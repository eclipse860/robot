import asyncio
import json

import websockets


PI_IP = "100.69.90.121"
PORT = 8765


async def main():
    uri = f"ws://{PI_IP}:{PORT}"

    async with websockets.connect(uri) as ws:
        print("Connected")

        sequence = [
            0.0,
            -1.0,
            1.0,
            0.0,
        ]

        for val in sequence:
            payload = {
                "steering": val,
                "throttle": 0.0,
            }
            await ws.send(json.dumps(payload))
            print("sent", payload)
            await asyncio.sleep(1.5)

        print("Done. Holding center for failsafe test...")
        await asyncio.sleep(2)


asyncio.run(main())
