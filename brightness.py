"""
Apple Studio Display Brightness Control for Windows
Based on https://github.com/himbeles/studi

Usage:
    py brightness.py                  # Set to default (20%)
    py brightness.py get              # Show current brightness %
    py brightness.py set 75           # Set to 75%
    py brightness.py up               # Increase by 10%
    py brightness.py down             # Decrease by 10%
    py brightness.py up --step 5      # Increase by 5%
"""

import sys
import struct
import hid

VENDOR_ID = 0x05AC                  # Apple
PRODUCT_IDS = (0x1116, 0x1114)      # Studio Display (newer, older)
INTERFACE_NR = 0x07                 # HID interface for brightness control
REPORT_ID = 0x01
REPORT_LEN = 7                      # report_id + 4 bytes brightness + 2 bytes padding

# Raw firmware brightness scale (not nits)
MIN_BRIGHTNESS = 400
MAX_BRIGHTNESS = 60000
BRIGHTNESS_RANGE = MAX_BRIGHTNESS - MIN_BRIGHTNESS

DEFAULT_PERCENT = 20
DEFAULT_STEP = 10


def fail(msg):
    print(f"Error: {msg}", file=sys.stderr)
    sys.exit(1)


def find_display():
    """Find the Apple Studio Display HID device on the brightness interface."""
    for pid in PRODUCT_IDS:
        for dev in hid.enumerate(VENDOR_ID, pid):
            if dev.get("interface_number") == INTERFACE_NR:
                return dev
    return None


def get_brightness_raw(device):
    """Read current brightness as a raw firmware value."""
    buf = device.get_feature_report(REPORT_ID, REPORT_LEN)
    if len(buf) < 5:
        raise RuntimeError(f"Unexpected report length: {len(buf)}")
    # Bytes 1-4 are brightness as little-endian u32
    return struct.unpack_from("<I", bytes(buf), 1)[0]


def get_brightness_percent(device):
    """Read current brightness as a percentage (0-100)."""
    raw = get_brightness_raw(device)
    return round((raw - MIN_BRIGHTNESS) / BRIGHTNESS_RANGE * 100)


def set_brightness_percent(device, percent):
    """Set brightness to a percentage (0-100). Returns the clamped percent."""
    percent = max(0, min(100, percent))
    raw = round(percent / 100 * BRIGHTNESS_RANGE + MIN_BRIGHTNESS)
    raw = max(MIN_BRIGHTNESS, min(MAX_BRIGHTNESS, raw))
    device.send_feature_report(struct.pack("<BI2x", REPORT_ID, raw))
    return percent


def parse_int(value, name):
    try:
        return int(value)
    except ValueError:
        fail(f"{name} must be a whole number, got '{value}'")


def parse_step():
    if "--step" not in sys.argv:
        return DEFAULT_STEP
    i = sys.argv.index("--step")
    if i + 1 >= len(sys.argv):
        fail("--step needs a value, e.g. --step 5")
    return parse_int(sys.argv[i + 1], "--step")


def main():
    args = sys.argv[1:]
    cmd = args[0].lower() if args else "set"

    if cmd in ("-h", "--help", "help"):
        print(__doc__.strip())
        return

    if cmd not in ("get", "set", "up", "down"):
        fail(f"Unknown command: {cmd}\nCommands: get, set, up, down")

    info = find_display()
    if not info:
        fail("No Apple Studio Display found. Check the USB-C/Thunderbolt connection.")

    device = hid.device()
    try:
        device.open_path(info["path"])
    except OSError as e:
        fail(f"Found the display but couldn't open it: {e}")

    try:
        if cmd == "get":
            print(f"Brightness: {get_brightness_percent(device)}%")

        elif cmd == "set":
            value = parse_int(args[1], "Brightness") if len(args) >= 2 else DEFAULT_PERCENT
            applied = set_brightness_percent(device, value)
            print(f"Brightness set to {applied}%")

        else:  # up / down
            step = parse_step() * (1 if cmd == "up" else -1)
            current = get_brightness_percent(device)
            new_val = set_brightness_percent(device, current + step)
            print(f"Brightness: {current}% -> {new_val}%")
    finally:
        device.close()


if __name__ == "__main__":
    main()
