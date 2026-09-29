# Pi web controller

The Pi serves the existing browser GUI and forwards commands to the UNO over
USB at 9600 baud. The UNO retains its independent 300 ms motion timeout.
The controller source remains in `tools/mac_web_controller.py` so the Mac and
Pi use the same implementation; web assets remain in `tools/web/`.

## Deploy from the Mac

Keep motor power OFF, leave the yellow PWR jumper removed, connect the UNO to
the Pi by USB, and close miniterm/Serial Monitor. Use a stable Pi power supply.

The Pi needs Python 3.10+ and pyserial. This project's Debian 13 Pi already had
`python3-serial` 3.5-2 installed at the last inspection. If absent, install it
on the Pi with `sudo apt install python3-serial`. No system-wide pip install is
needed. The deployment helper checks the import before copying anything.

From the project folder on your Mac:

```bash
bash pi/deploy.sh YOUR_USER@robotcar.local
```

Enter the Pi account password locally when SSH/scp requests it. Only runtime
files are copied into a new `~/robotcar/releases/` directory, and
`~/robotcar/current` points to that release. Previous releases are retained.
The helper does not start the controller or install an automatic boot service.
Do not deploy over a running control session; stop the server first so Python
and browser files remain from the same release.

Start the controller in a foreground SSH session:

```bash
ssh -t YOUR_USER@robotcar.local 'bash ~/robotcar/current/pi/run.sh'
```

Open `http://robotcar.local:8765` in a browser on the same trusted network.
If local hostname lookup is unavailable, use the Pi's current Wi-Fi IP instead.
Keep the SSH terminal open; Ctrl+C stops the server and sends a stop command.
SSH disconnection is not a verified service-lifecycle mechanism: always stop
explicitly and turn motor power off when finished.

## Selecting the UNO

The controller prefers `/dev/serial/by-id/` on Linux. It refuses ambiguous
multiple-device selection instead of probing devices. To choose explicitly:

```bash
ls -l /dev/serial/by-id/
bash ~/robotcar/current/pi/run.sh --port /dev/serial/by-id/YOUR_UNO_PORT
```

Run this in a Pi SSH terminal, replacing the placeholder with the actual entry.
Only one process may use the UNO port. If access is denied, check that the Pi
user belongs to `dialout`; adding that group requires a fresh login. The normal
controller must not run as root. `ROBOTCAR_PYTHON` may select a virtual-environment
Python containing pyserial if a dedicated environment is preferred.

## Network and command behavior

- The Pi launcher listens on all IPv4 interfaces, port 8765. The direct Python
  command still defaults to loopback for the existing Mac workflow.
- This is an unauthenticated trusted-LAN prototype. Any peer that can reach it
  can request control or stop. Do not forward its port to the internet.
- Browser requests must include the expected header and, when supplied, a
  matching Origin. This blocks ordinary cross-site browser requests, but is
  not a login or protection from other local-network users.
- A short-lived control token permits one active browser at a time. Movement
  commands are sent every 100 ms; the server does not generate movement on its
  own. A 300 ms gap expires control and sends stop; a fresh press is required.
- Sequence numbers reject reordered commands. Releasing control invalidates
  its token, so late commands cannot revive that session. Heartbeats are not
  queued in the browser. Requests that take too long cancel local movement.
- X/Space is a global stop, including from another browser. Ordinary release
  targets only its own session. The UNO independently releases motors about
  300 ms after the last received motion command if the Pi stops communicating.
- These are software timeouts, not guaranteed physical stopping distances.
  Releasing a motor is not active braking. Network/OS delays must be tested.
- USB errors mark the controller disconnected; reconnect the board and restart
  the server. It does not automatically resume motion after recovery.

## First hardware validation

1. With motor power off, open the page and check that it reports the UNO
   connected. Confirm commands and STOP/TIMEOUT messages without wheel motion.
2. Confirm stable Pi voltage and correct separate motor power at EXT_PWR with
   the jumper removed. Raise the wheels, then enable motor power.
3. Briefly hold Forward and release. Verify actual stopping, then test the
   other directions and explicit X/Space stop.
4. Verify stopping after tab blur/close, Wi-Fi loss, server termination, and USB
   removal. Check that reconnecting never resumes motion by itself.
5. Open a second browser: it must not take over while the first is driving;
   its explicit stop should still work. Record observations and power readings.
6. Switch motor power off and stop the foreground server when finished.

The user subsequently confirmed the tuned firmware and Pi GUI worked. Automatic
startup is added below; its first installation and reboot check remain to be done.

## Development checks

From the project root, with pyserial installed in the selected Python:

```bash
python3 -m unittest discover -s tests -p 'test_*.py' -v
node tests/test_web_client.cjs
bash -n pi/deploy.sh pi/run.sh
```

Python tests use a fake UNO and local HTTP server. JavaScript tests exercise
release during acquisition, in-flight commands, emergency stop, and single-shot
controls. No test opens a physical serial device or sends a real motor command.

## Update after the successful driving test

The user confirmed Pi/browser motor control worked. This tuning revision is
locally tested but still needs deployment and physical validation.

1. Stop the Pi controller with Ctrl+C and turn motor power off.
2. Move the UNO USB connection from Pi to Mac. In Arduino IDE open
   `firmware/uno/manual_serial_control/manual_serial_control.ino`, select
   Arduino Uno and its port, and upload. Close Serial Monitor afterward.
3. Reconnect UNO USB to the Pi, keeping the yellow PWR jumper removed.
4. From the Mac project directory run `bash pi/deploy.sh soheilito@robotcar.local`.
5. Run `ssh -t soheilito@robotcar.local 'bash ~/robotcar/current/pi/run.sh'`.
6. Refresh the browser at `http://robotcar.local:8765`. Confirm PWM 195 and
   curve strength 75% before enabling motor power and testing.

Messages now appear newest first in a bounded panel. The bench notice is
removed. PWM spans 195–255, with 5-point +/- steps and nine presets. Curve
strength is adjustable from 0–100%; 50% reproduces the previous behavior.
A firmware mismatch blocks driving and requests the updated UNO sketch.

Battery sensing requires additional wiring; see
[the battery monitoring design](../docs/BATTERY_MONITORING.md). No voltage
measurement or battery warning is implemented yet.

## Automatic startup: open the browser and drive

One-time setup: turn motor power off, stop the foreground controller with
Ctrl+C, and leave the UNO connected by USB. From the Mac:

```bash
cd /Users/MyWorld/RobotCar-EdgeAI
bash pi/deploy.sh soheilito@robotcar.local
ssh -t soheilito@robotcar.local 'sudo bash ~/robotcar/current/pi/install-service.sh'
```

Enter passwords locally when prompted. The installer enables `robotcar.service`
at boot, starts it now, and checks the UNO's readiness. It runs the controller
as the normal Pi account with serial access, not root. If UNO is missing at
boot, startup retries every five seconds. Binding all local interfaces lets
Wi-Fi become available after process startup. This remains a trusted-LAN
controller, with the same URL and access policy as before.

After setup, close the terminal. On each use, power on the Pi with UNO attached,
wait for Wi-Fi and startup, then visit `http://robotcar.local:8765` from the same
network. Bookmark it or add it to the phone home screen. No UNO firmware change
is required for automatic startup. Motors remain stopped until a fresh control
press. A service restart does not restore an earlier movement command.

Verify once with motor power off: reboot the Pi, close SSH, reopen the page,
and confirm UNO connected without starting anything manually. Then test a
brief movement and release with the wheels raised. The first installation and
reboot verification must be confirmed on the actual Pi.

Maintenance commands on the Pi:

```bash
sudo systemctl status robotcar --no-pager
sudo journalctl -u robotcar -n 40 --no-pager
sudo systemctl stop robotcar     # before UNO uploads or another serial tool
sudo systemctl start robotcar   # after the upload
sudo systemctl restart robotcar # after reconnecting a disconnected UNO
sudo systemctl disable --now robotcar # remove automatic startup
```

For future deployments, stop the service before running `pi/deploy.sh`, then
start it again. Do not run `pi/run.sh` manually while the service owns the port.
A USB failure after startup still requires a service restart; missing USB at
boot is retried automatically. Switching off motor power after use and cleanly
shutting down the Pi remain separate from closing the browser.
