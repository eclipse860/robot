# Robot Control

Small Raspberry Pi robot control project using an Adafruit PCA9685 PWM driver for steering servo and ESC output.

## Current Status

- Local steering servo test is fixed and can run finite cycles or continuously.
- Project runner script `./robot` is available for servo, motor, ESC calibration, and ESC pulse diagnostics.
- ESC throttle endpoints have been calibrated from the PCA9685.
- Forward and reverse motor tests are working on the real robot.
- Real-robot wheel-start thresholds are about `1.64 ms` forward and `1.35 ms` reverse.

## Hardware

- Raspberry Pi I2C on `board.SCL` and `board.SDA`
- Adafruit PCA9685 at `50 Hz`
- Steering servo on PCA9685 channel `0`
- ESC throttle signal on PCA9685 channel `1`
- Steering pulse defaults:
  - Left: `1.20 ms`
  - Center: `1.50 ms`
  - Right: `1.80 ms`
- ESC pulse defaults:
  - Neutral: `1.50 ms`
  - Forward wheel-start on the real robot: about `1.64 ms`
  - Reverse wheel-start on the real robot: about `1.35 ms`

The earlier motor test used a bench motor. On the real robot, the wheels did not begin turning until about `1.64 ms` forward and `1.35 ms` reverse. Reverse motion at `1.35 ms` is very slow.

## Environment

The project runner defaults to this Python virtual environment:

```sh
/home/phil/robot-env/bin/python
```

Override it with `ROBOT_PYTHON` if needed:

```sh
ROBOT_PYTHON=/path/to/python ./robot servo-test --cycles 1
```

## Local Hardware Tests

Run commands from the repository root:

```sh
cd /home/phil/robot
```

Run one finite steering servo test cycle:

```sh
./robot servo-test --cycles 1
```

Run the servo test continuously:

```sh
./robot servo-test --forever
```

Run the conservative forward motor test:

```sh
./robot motor-test --armed
```

Run the conservative reverse motor test:

```sh
./robot motor-test --armed --reverse
```

Hold an ESC diagnostic pulse interactively:

```sh
./robot esc-pulse --armed --pulse-ms 1.50
```

## ESC Calibration

The ESC has been calibrated from the PCA9685 using:

```sh
./robot esc-calibrate --armed
```

The calibration script guides the QUICRUN WP 1080 G2 through neutral, full forward, full brake/reverse, and back to neutral. Keep the robot lifted, keep the motor area clear, disconnect the ESC red receiver/BEC wire from the PCA9685 side, and use common ground between the ESC signal ground, PCA9685, Pi, and supply negative.

## WebSocket Server

Start the WebSocket control server on robot hardware:

```sh
/home/phil/robot-env/bin/python network/ws_server.py
```

The server listens on `0.0.0.0:8765` and accepts JSON messages:

```json
{"steering": 0.0, "throttle": 0.0}
```

Steering is clamped to `-1.0..1.0`. Throttle is clamped to `0.0..1.0`.
