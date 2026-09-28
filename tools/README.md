# Mac Web Controller

The [Mac web controller](mac_web_controller.py) connects directly to the UNO
over USB and opens a local control page. The page detects key press and release
events, highlights the active key, sends movement commands every 100 ms while
a movement key is held, and sends `x` immediately when it is released. This
works with the 300 ms watchdog in
[manual_serial_control.ino](../firmware/uno/manual_serial_control/manual_serial_control.ino).

The page and controller listen only on the Mac itself at
`http://127.0.0.1:8765`; they are not exposed to the local network.

## One-time setup

Open Terminal and run:

```bash
cd RobotCar-EdgeAI
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install -r tools/requirements-web.txt
```

## Run

1. Upload `manual_serial_control.ino` to the UNO.
2. Close Arduino Serial Monitor so it releases the serial port.
3. Keep the wheels raised for the first powered test.
4. Connect the UNO directly to the Mac by USB.
5. In Terminal, run:

```bash
cd RobotCar-EdgeAI
source .venv/bin/activate
python3 tools/mac_web_controller.py
```

The controller finds `/dev/cu.usbmodem...` automatically and opens the web
page. If multiple USB serial devices are connected, select the UNO explicitly:

```bash
python3 tools/mac_web_controller.py --port /dev/cu.usbmodem101
```

Keep the control page active while driving. Hold `W`, `A`, `S`, or `D` and
release the key to stop. `Q`, `E`, `Z`, and `C` select curved movements.
The on-screen controls also work with a mouse or trackpad. `X` or Space sends
an immediate stop.

The Messages panel shows serial connection events, commands, UNO responses,
warnings, and errors. Closing the controller with `Control-C` sends a final
stop command and closes the serial port.

Do not leave Arduino Serial Monitor open at the same time. Only one program can
own the UNO serial port.

## Next: Pi-hosted control

As of 2026-09-28, the user has confirmed motor operation through the Pi's USB
serial connection to the UNO. The next step is to reuse this controller and
its existing web assets on the Pi, with browser access from the local network.
The current loopback binding does not provide that access yet.

Follow the [Pi deployment checklist](../docs/PI_SETUP.md#next-milestone-reuse-the-existing-web-gui-on-the-pi)
for listen-address configuration, stable Linux serial paths, headless startup,
and stopping/power validation. This is planned work, not a completed deployment.
