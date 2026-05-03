# Changelog

All notable changes to this robot project should be recorded here before committing to Git.

## v0.1.0 - 2026-04-29

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
- Noted then-current ESC limitation: throttle was not enabled in the Pi server and ESC compatibility still needed confirmation.

## v0.2.0 - 2026-05-02

- Initialized the local robot project Git repository on branch `main`.
- Added the WebSocket control server for steering and throttle output through a PCA9685.
- Added a manual steering servo sweep test script.
- Added a project `.gitignore` for Python caches, local environments, and local Codex/runtime artifacts.

## v0.3.0 - 2026-05-03

- Improved the local PCA9685 servo test with command-line options, finite cycles by default, and cleanup that recenters the servo.
- Added a `./robot servo-test` project runner command for shorter local hardware test commands.
- Added a conservative `./robot motor-test --armed` command for PCA9685-to-ESC drive motor testing.
- Added a guided `./robot esc-calibrate --armed` command for QUICRUN WP 1080 G2 throttle endpoint calibration.
- Added a fixed `./robot esc-pulse --armed --pulse-ms <value>` diagnostic command for holding ESC PWM pulses during troubleshooting.
- Updated the conservative motor test default to the real-robot forward start threshold of `1.64 ms`.
- Added a timed reverse mode to `./robot motor-test --armed --reverse` for lifted-wheel ESC testing.
- Updated the reverse motor test default to the real-robot reverse start threshold of `1.35 ms`.
- Documented the hardware layout, setup, local test commands, ESC calibration result, and measured forward/reverse wheel-start thresholds in `README.md`.
