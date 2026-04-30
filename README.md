# Remote Robot

Raspberry Pi 5 based remote robot control project. The Pi drives a PCA9685 PWM board over I2C for steering and exposes a WebSocket server for commands from a Windows PC over Tailscale. A separate systemd service streams the Pi camera as MJPEG over TCP for VLC.

## Hardware

- Raspberry Pi 5
- PCA9685 PWM servo driver
- Steering servo on PCA9685 channel 0
- Buck converter providing 5-6 V to PCA9685 V+
- LiPo battery for onboard power
- Pi camera
- Windows PC running the control sender

Current tested control path:

```text
Windows ws_send.py -> Tailscale -> Pi WebSocket server -> PCA9685 CH0 -> steering servo
```

The ESC/throttle path is not enabled in the current Pi server code. The PC sender includes a `throttle` field, but `network/ws_server.py` currently ignores it.

## Repository Layout

```text
network/ws_server.py         Pi WebSocket server for steering control
tests/servo_test.py          Direct Pi/PCA9685 steering servo test
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

## Windows PC Setup

Install Python 3, then install the sender dependency:

```powershell
python -m pip install -r requirements-pc.txt
```

Update `PI_IP` in `pc/ws_send.py` if the Pi Tailscale IP changes.

## Direct Servo Test

Run this on the Pi with the robot safely lifted so the steering can move freely:

```bash
cd ~/robot
/home/phil/robot-env/bin/python tests/servo_test.py
```

The servo should repeat center, left, and right movement.

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

## Bad Message Test

Sending a plain text message such as `hello from Windows` should not move the robot. The Pi should log a bad input message and center the steering:

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

## Verified Status

The following functions have been tested successfully:

- PCA9685 detected on I2C at `0x40`
- `robot-ws.service` running and listening on `0.0.0.0:8765`
- Windows WebSocket sender connects over Tailscale
- Steering servo moves from PC commands
- Steering returns to center after sender disconnects
- Camera stream works in VLC over `tcp://100.69.90.121:8888`

## ESC Status

ESC throttle is intentionally not enabled yet. Before adding throttle control, confirm the ESC signal requirements, arming sequence, neutral point, and whether it accepts 3.3 V logic from the PCA9685 signal output.
