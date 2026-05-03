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

## v0.4.0 - 2026-05-03

- Refactored `network/ws_server.py` so importing it no longer initializes Raspberry Pi I2C or PCA9685 hardware.
- Added a `RobotOutputs` hardware adapter and `create_outputs()` factory for runtime PCA9685 setup.
- Added unit tests for WebSocket server pulse conversion, steering/throttle mapping, safe output behavior, and JSON command application.
- Added `tests/__init__.py` so standard `unittest discover` finds the automated tests.

## v0.5.0 - 2026-05-03

- Moved real robot hardware scripts from `tests/` to `hardware_tests/` so automated tests and hardware exercises are clearly separated.
- Added a menu-driven hardware test launcher available through `./robot menu` or `./robot hardware-menu`.
- Kept the existing direct hardware test commands working through `./robot servo-test`, `./robot motor-test`, `./robot esc-calibrate`, and `./robot esc-pulse`.
- Added `./robot test` for automated unit tests and `./robot check` for syntax checks.
- Added `pyproject.toml` with project metadata and optional Raspberry Pi / PC dependency groups.
- Updated `README.md` with the new layout, menu command, and test/check commands.

## v0.6.0 - 2026-05-03

- Added an async WebSocket handler test that verifies the watchdog failsafe returns steering and throttle to safe outputs when a connected client goes idle.

## v0.7.0 - 2026-05-03

- Added a menu option to run the automated robot test suite from the interactive launcher.
- The menu now describes the automated test coverage before running the suite.
- Updated `README.md` to note that the menu can run automated tests.

## v0.8.0 - 2026-05-03

- Updated the WebSocket control contract so throttle commands are signed from `-1.0` reverse/brake through `0.0` neutral to `1.0` forward.
- Added automated tests for reverse throttle mapping and command application.
- Added `pc/keyboard_send.py` for continuous Windows keyboard control over Tailscale.
- Added root-level `keyboard_send.py` and `ws_send.py` scripts for Windows checkouts where commands are run from `C:\code\robot`.
- The keyboard sender sends neutral throttle and centered steering when exiting.
- Updated `./robot check` to syntax-check PC control scripts.
- Updated README and PC-side documentation with keyboard controls, conservative default limits, and signed throttle behavior.
- Bumped `pyproject.toml` project metadata to `0.8.0`.
