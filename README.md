# Remote Robot

Raspberry Pi 5 based remote robot control project. The Pi drives a PCA9685 PWM board over I2C for steering servo and ESC output, exposes a WebSocket server for commands from a Windows PC over Tailscale, and can stream the Pi camera as MJPEG over TCP for VLC.

## Current Status

- PCA9685 is detected on I2C at `0x40`.
- Local steering servo test is fixed and can run finite cycles or continuously.
- Windows WebSocket sender can command steering over Tailscale.
- Steering returns to center after the sender disconnects.
- Camera stream works in VLC over TCP port `8888`.
- Project runner script `./robot` is available for servo, motor, ESC calibration, and ESC pulse diagnostics.
- ESC throttle endpoints have been calibrated from the PCA9685.
- Forward and reverse motor tests are working on the real robot.
- Real-robot wheel-start thresholds are about `1.64 ms` forward and `1.35 ms` reverse.

## Hardware

- Raspberry Pi 5
- PCA9685 PWM servo driver at `50 Hz`
- Steering servo on PCA9685 channel `0`
- ESC throttle signal on PCA9685 channel `1`
- Buck converter providing 5-6 V to PCA9685 V+
- LiPo battery for onboard power
- Pi camera
- Windows PC running the control sender

Current tested control path:

```text
Windows ws_send.py -> Tailscale -> Pi WebSocket server -> PCA9685 -> steering servo / ESC
```

Steering pulse defaults:

- Left: `1.20 ms`
- Center: `1.50 ms`
- Right: `1.80 ms`

ESC pulse defaults:

- Neutral: `1.50 ms`
- Forward wheel-start on the real robot: about `1.64 ms`
- Reverse wheel-start on the real robot: about `1.35 ms`

The earlier motor test used a bench motor. On the real robot, the wheels did not begin turning until about `1.64 ms` forward and `1.35 ms` reverse. Reverse motion at `1.35 ms` is very slow.

## Repository Layout

```text
network/ws_server.py         Pi WebSocket server for steering and throttle control
tests/servo_test.py          Direct Pi/PCA9685 steering servo test
tests/motor_test.py          Direct Pi/PCA9685 ESC motor test
tests/esc_calibrate.py       Guided ESC endpoint calibration
tests/esc_pulse.py           Interactive ESC pulse diagnostic
pc/ws_send.py                Windows WebSocket command sender
requirements-rpi.txt         Python dependencies for the Raspberry Pi
requirements-pc.txt          Python dependencies for the Windows PC sender
systemd/robot-ws.service     WebSocket service template
systemd/robot-cam.service    Camera stream service template
CHANGELOG.md                 Project change log
```

## Raspberry Pi Setup

Enable I2C using `raspi-config`, then verify that the PCA9685 appears at address `0x40`:

```bash
i2cdetect -y 1
```

Create and activate the Python environment:

```bash
python3 -m venv ~/robot-env
source ~/robot-env/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements-rpi.txt
```

Install camera tools if needed:

```bash
sudo apt install -y rpicam-apps
```

Install I2C tools if needed:

```bash
sudo apt install -y i2c-tools
```

The project runner defaults to:

```bash
/home/phil/robot-env/bin/python
```

Override it with `ROBOT_PYTHON` if needed:

```bash
ROBOT_PYTHON=/path/to/python ./robot servo-test --cycles 1
```

## Windows PC Setup

### Tailscale

Download and install Tailscale from:

```text
https://tailscale.com/download/windows
```

Log in with Google using the Eclipse860 account.

### Python Install

Open PowerShell as Administrator:

```powershell
winget install Python.Python.3.13
```

Exit PowerShell, then relaunch PowerShell so the updated Python path is loaded.

### Websockets Install

Install the Python WebSocket dependency:

```powershell
pip install websockets
```

You can also install from the repo dependency file:

```powershell
python -m pip install -r requirements-pc.txt
```

### VLC

Install VLC from the Windows App Store.

Update `PI_IP` in `pc/ws_send.py` if the Pi Tailscale IP changes.

## Local Hardware Tests

Run commands from the repository root:

```bash
cd /home/phil/robot
```

Run one finite steering servo test cycle:

```bash
./robot servo-test --cycles 1
```

Run the servo test continuously:

```bash
./robot servo-test --forever
```

Run the conservative forward motor test:

```bash
./robot motor-test --armed
```

Run the conservative reverse motor test:

```bash
./robot motor-test --armed --reverse
```

Hold an ESC diagnostic pulse interactively:

```bash
./robot esc-pulse --armed --pulse-ms 1.50
```

## ESC Calibration

The ESC has been calibrated from the PCA9685 using:

```bash
./robot esc-calibrate --armed
```

The calibration script guides the QUICRUN WP 1080 G2 through neutral, full forward, full brake/reverse, and back to neutral. Keep the robot lifted, keep the motor area clear, disconnect the ESC red receiver/BEC wire from the PCA9685 side, and use common ground between the ESC signal ground, PCA9685, Pi, and supply negative.

## Tailscale VPN Test

On the Pi, check that Tailscale is active:

```bash
systemctl status tailscaled --no-pager
```

Look for `active (running)`.

Gather the Pi Tailscale IP:

```bash
tailscale status
```

The Pi Tailscale IP should be listed in the output.

On the Windows PC:

- Confirm the Tailscale app is running in the system tray.
- Confirm the PC Tailscale IP in the Tailscale app.
- You can also check the PC Tailscale IP with `ipconfig`.

From Windows PowerShell, verify that the PC can reach the robot:

```powershell
ping 100.69.90.121
```

Replace `100.69.90.121` with the current Pi Tailscale IP if it changed.

## WebSocket Steering Test

Check that the WebSocket service is running on the Pi:

```bash
systemctl status robot-ws.service --no-pager
ss -lntp | grep 8765
```

Watch live logs:

```bash
sudo journalctl -u robot-ws.service -f
```

From Windows:

```powershell
cd C:\code\robot\pc
python ws_send.py
```

Expected behavior:

- The PC connects and sends center, left, right, center.
- The Pi log shows `RX steering=...` messages.
- The servo returns to center after the client exits.

## WebSocket Server

Start the WebSocket control server on robot hardware:

```bash
/home/phil/robot-env/bin/python network/ws_server.py
```

The server listens on `0.0.0.0:8765` and accepts JSON messages:

```json
{"steering": 0.0, "throttle": 0.0}
```

Steering is clamped to `-1.0..1.0`. Throttle is clamped to `0.0..1.0`.

## Bad Message Test

Sending a plain text message such as `hello from Windows` should not move the robot. The Pi should log a bad input message and center steering/throttle:

```text
Bad input -> centered: ...
```

This can be watched with:

```bash
sudo journalctl -u robot-ws.service -f
```

## Camera Test

Check the camera service:

```bash
systemctl status robot-cam.service --no-pager
ss -lntp | grep 8888
```

Open VLC on Windows with:

```text
tcp://100.69.90.121:8888
```

Use VLC options:

```text
:network-caching=1000 :demux=mjpeg
```

## Systemd Services

Service templates are tracked in `systemd/`. To install them on the Pi:

```bash
sudo cp systemd/robot-ws.service /etc/systemd/system/robot-ws.service
sudo cp systemd/robot-cam.service /etc/systemd/system/robot-cam.service
sudo systemctl daemon-reload
sudo systemctl enable --now robot-ws.service
sudo systemctl enable --now robot-cam.service
```
