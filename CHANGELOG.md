# Changelog

## 2026-04-29

- Verified PCA9685 detection on Raspberry Pi I2C bus at address `0x40`.
- Verified `robot-ws.service` is running and listening on port `8765`.
- Verified Windows WebSocket sender can command steering over Tailscale.
- Verified steering servo moves center, left, right, and returns to center.
- Verified WebSocket disconnect failsafe centers steering.
- Verified camera stream works in VLC over TCP port `8888`.
- Added Raspberry Pi and Windows Python dependency files.
- Added root README with hardware, setup, service, and test instructions.
- Added tracked systemd service templates for WebSocket and camera services.
- Moved Pi code to repo-root `network/` and `tests/` paths to match the active Pi deployment layout.

## Current Limitations

- Throttle/ESC control is not enabled in the Pi server code.
- `pc/ws_send.py` sends a `throttle` field, but the current server ignores it.
- ESC compatibility still needs confirmation before motor throttle testing.
