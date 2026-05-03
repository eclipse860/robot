import subprocess
import sys
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]
HARDWARE_TEST_DIR = ROOT_DIR / "hardware_tests"


def run_script(script_name, *args):
    script_path = HARDWARE_TEST_DIR / script_name
    subprocess.run([sys.executable, str(script_path), *args], check=False)


def run_robot_command(*args):
    subprocess.run([str(ROOT_DIR / "robot"), *args], check=False)


def confirm_armed():
    print()
    print("Safety check:")
    print("- Robot is lifted or wheels are clear.")
    print("- Motor area is clear.")
    print("- ESC red receiver/BEC wire is disconnected from the PCA9685 side.")
    print("- ESC signal/ground and common ground are connected correctly.")
    answer = input("Type ARMED to continue: ").strip()
    return answer == "ARMED"


def ask_float(prompt, default_value, min_value=None, max_value=None):
    while True:
        raw = input(f"{prompt} [{default_value}]: ").strip()
        if not raw:
            return default_value
        try:
            value = float(raw)
        except ValueError:
            print("Enter a number.")
            continue
        if min_value is not None and value < min_value:
            print(f"Value must be at least {min_value}.")
            continue
        if max_value is not None and value > max_value:
            print(f"Value must be no more than {max_value}.")
            continue
        return value


def ask_int(prompt, default_value, min_value=None):
    while True:
        raw = input(f"{prompt} [{default_value}]: ").strip()
        if not raw:
            return default_value
        try:
            value = int(raw)
        except ValueError:
            print("Enter a whole number.")
            continue
        if min_value is not None and value < min_value:
            print(f"Value must be at least {min_value}.")
            continue
        return value


def run_servo_cycle():
    cycles = ask_int("Servo cycles", 1, min_value=1)
    run_script("servo_test.py", "--cycles", str(cycles))


def run_servo_forever():
    run_script("servo_test.py", "--forever")


def run_motor(reverse=False):
    if not confirm_armed():
        print("Canceled.")
        return
    args = ["--armed"]
    if reverse:
        args.append("--reverse")
    run_script("motor_test.py", *args)


def run_esc_calibration():
    if not confirm_armed():
        print("Canceled.")
        return
    run_script("esc_calibrate.py", "--armed")


def run_esc_pulse():
    if not confirm_armed():
        print("Canceled.")
        return
    pulse_ms = ask_float("Starting pulse in ms", 1.50, min_value=1.0, max_value=2.0)
    run_script("esc_pulse.py", "--armed", "--pulse-ms", f"{pulse_ms:.2f}")


def run_automated_tests():
    print()
    print("Running automated robot tests:")
    print("- PWM pulse width to duty-cycle conversion")
    print("- Steering pulse mapping and clamping")
    print("- Throttle pulse mapping and clamping")
    print("- Safe output behavior")
    print("- WebSocket JSON command parsing")
    print("- Bad input rejection")
    print("- WebSocket idle-client watchdog failsafe")
    print()
    run_robot_command("test")


def main():
    actions = {
        "1": ("Servo test, finite cycles", run_servo_cycle),
        "2": ("Servo test, run until Ctrl-C", run_servo_forever),
        "3": ("Motor test, small forward", lambda: run_motor(reverse=False)),
        "4": ("Motor test, small reverse", lambda: run_motor(reverse=True)),
        "5": ("ESC pulse diagnostic", run_esc_pulse),
        "6": ("ESC calibration", run_esc_calibration),
        "7": ("Run automated robot tests", run_automated_tests),
        "q": ("Quit", None),
    }

    while True:
        print()
        print("Robot Hardware Test Menu")
        for key, (label, _action) in actions.items():
            print(f"  {key}. {label}")

        choice = input("Select option: ").strip().lower()
        if choice == "q":
            return
        action = actions.get(choice)
        if action is None:
            print("Unknown option.")
            continue
        action[1]()


if __name__ == "__main__":
    main()
