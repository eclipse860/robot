#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PYTHON="${ROBOT_PYTHON:-/home/phil/robot-env/bin/python}"

cd "$ROOT_DIR"

case "${1:-}" in
  servo-test)
    shift
    exec "$PYTHON" "$ROOT_DIR/hardware_tests/servo_test.py" "$@"
    ;;
  motor-test)
    shift
    exec "$PYTHON" "$ROOT_DIR/hardware_tests/motor_test.py" "$@"
    ;;
  esc-calibrate)
    shift
    exec "$PYTHON" "$ROOT_DIR/hardware_tests/esc_calibrate.py" "$@"
    ;;
  esc-pulse)
    shift
    exec "$PYTHON" "$ROOT_DIR/hardware_tests/esc_pulse.py" "$@"
    ;;
  menu|hardware-menu)
    shift
    exec "$PYTHON" "$ROOT_DIR/hardware_tests/menu.py" "$@"
    ;;
  test)
    shift
    exec "$PYTHON" -m unittest discover "$@"
    ;;
  check)
    shift
    exec "$PYTHON" -m py_compile \
      "$ROOT_DIR/network/ws_server.py" \
      "$ROOT_DIR/hardware_tests/servo_test.py" \
      "$ROOT_DIR/hardware_tests/motor_test.py" \
      "$ROOT_DIR/hardware_tests/esc_calibrate.py" \
      "$ROOT_DIR/hardware_tests/esc_pulse.py" \
      "$ROOT_DIR/hardware_tests/menu.py" \
      "$ROOT_DIR/keyboard_send.py" \
      "$ROOT_DIR/pc/keyboard_send.py" \
      "$ROOT_DIR/pc/ws_send.py" \
      "$ROOT_DIR/ws_send.py" \
      "$ROOT_DIR/tests/test_ws_server.py"
    ;;
  *)
    echo "Usage:"
    echo "  ./robot menu"
    echo "  ./robot test"
    echo "  ./robot check"
    echo "  ./robot servo-test [servo_test.py options]"
    echo "  ./robot motor-test --armed [motor_test.py options]"
    echo "  ./robot esc-calibrate --armed [esc_calibrate.py options]"
    echo "  ./robot esc-pulse --armed --pulse-ms <1.0..2.0>"
    echo
    echo "Examples:"
    echo "  ./robot menu"
    echo "  ./robot test"
    echo "  ./robot check"
    echo "  ./robot servo-test --cycles 1"
    echo "  ./robot servo-test --forever"
    echo "  ./robot esc-calibrate --armed"
    echo "  ./robot esc-pulse --armed --pulse-ms 2.00"
    echo "  ./robot motor-test --armed"
    exit 2
    ;;
esac
