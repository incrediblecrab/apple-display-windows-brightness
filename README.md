# Apple Studio Display brightness control for Windows

Windows has no built-in way to change the brightness of an Apple Studio Display. This script does it over USB HID, the same way macOS does. It is based on [himbeles/studi](https://github.com/himbeles/studi).

## Setup

You need Python 3 and the `hidapi` package:

```
py -m pip install -r requirements.txt
```

## Usage

```
py brightness.py                  # Set to default (20%)
py brightness.py get              # Show current brightness %
py brightness.py set 75           # Set to 75%
py brightness.py up               # Increase by 10%
py brightness.py down             # Decrease by 10%
py brightness.py up --step 5      # Increase by 5%
```

## How it works

The display exposes brightness as a HID feature report on interface 7 (Apple vendor ID `0x05AC`, product ID `0x1116` or `0x1114`). The report is a report ID byte, a little-endian 32-bit brightness value, and 2 bytes of padding. The firmware's brightness scale runs from 400 to 60000, and the script maps it to 0-100%.

## Shortcut command

To set the brightness with one word, put a small `.cmd` file in a folder on your `PATH`. For example, `xdr.cmd`:

```bat
@py "C:\path\to\brightness.py" set 20
```
