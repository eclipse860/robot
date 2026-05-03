#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PYTHON="${ROBOT_PYTHON:-/home/phil/robot-env/bin/python}"

case "${1:-}" in
  servo-test)
    shift
    exec "$PYTHON" "$ROOT_DIR/tests/servo_test.py" "$@"
    ;;
  motor-test)
    shift
    exec "$PYTHON" "$ROOT_DIR/tests/motor_test.py" "$@"
    ;;
  esc-calibrate)
    shift
    exec "$PYTHON" "$ROOT_DIR/tests/esc_calibrate.py" "$@"
    ;;
  esc-pulse)
    shift
    exec "$PYTHON" "$ROOT_DIR/tests/esc_pulse.py" "$@"
    ;;
  *)
    echo "Usage:"
    echo "  ./robot servo-test [servo_test.py options]"
    echo "  ./robot motor-test --armed [motor_test.py options]"
    echo "  ./robot esc-calibrate --armed [esc_calibrate.py options]"
    echo "  ./robot esc-pulse --armed --pulse-ms <1.0..2.0>"
    echo
    echo "Examples:"
    echo "  ./robot servo-test --cycles 1"
    echo "  ./robot servo-test --forever"
    echo "  ./robot esc-calibrate --armed"
    echo "  ./robot esc-pulse --armed --pulse-ms 2.00"
    echo "  ./robot motor-test --armed"
    exit 2
    ;;
esac
