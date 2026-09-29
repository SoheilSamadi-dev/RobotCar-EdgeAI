# Pi operation and maintenance

For the initial build, follow the [setup guide](../docs/GETTING_STARTED.md).
These commands assume deployment to `~/robotcar/current`. Replace `YOUR_USER`
and `robotcar.local` with your Pi account and hostname or local IP address.

## Foreground operation

From your development computer:

```bash
ssh -t YOUR_USER@robotcar.local 'bash ~/robotcar/current/pi/run.sh'
```

Open `http://robotcar.local:8765`. Keep the terminal open; Ctrl+C stops the server
and sends stop. Turn motor power off when finished. A closed browser or SSH
connection is not a verified Pi shutdown mechanism.

## Automatic startup

The installer is implemented; installation and reboot validation are still
unconfirmed on the reference hardware. Complete the setup guide's manual checks
before using it.

With motor power OFF, stop the foreground controller with Ctrl+C and leave UNO
USB connected. Run from your development computer:

```bash
ssh -t YOUR_USER@robotcar.local 'sudo bash ~/robotcar/current/pi/install-service.sh'
```

The installer enables and starts `robotcar.service`, runs the controller as the
normal Pi account, and checks UNO readiness. Missing UNO at startup is retried
every five seconds. A USB failure after startup requires a service restart.

Verify with motor power off: reboot the Pi, reconnect the browser after Wi-Fi
returns, and confirm the UNO is connected without starting the server manually.
Then repeat raised-wheel movement and stop checks. Service restarts must not
resume old movement. Once verified, routine use is power-on, wait for Wi-Fi,
and open the browser URL.

## Update an installation

1. Turn motor power off and stop the controller. For a managed service, run
   `sudo systemctl stop robotcar` on the Pi; for foreground operation use Ctrl+C.
2. Upload the repository's UNO sketch if the firmware changed. Close Serial
   Monitor and reconnect UNO USB to the Pi.
3. From the project folder on the development computer, run
   `bash pi/deploy.sh YOUR_USER@robotcar.local`.
4. Run `sudo systemctl start robotcar` on the Pi, or start foreground operation.
5. Refresh the browser and repeat the connection, configuration, and stop checks.

Deployment retains previous releases and changes the `~/robotcar/current`
symlink. It does not start or stop the controller. Stop before deploying so
Python and browser assets come from the same release. Only one process can
own the UNO serial port.

## Troubleshooting

| Symptom | Check |
|---|---|
| Hostname not found | Substitute the Pi's LAN IP in SSH commands and the browser URL |
| Page unavailable | Confirm server/service is running, port 8765 is reachable, and Wi-Fi has no client isolation |
| No UNO | Check USB data cable, UNO power, and `/dev/serial/by-id/` |
| Serial permission denied | Confirm `dialout` membership and reconnect after changing groups |
| Port busy | Close Serial Monitor/miniterm and stop another running controller |
| Firmware mismatch | Upload this checkout's UNO sketch, restart the server, and refresh the browser |
| USB disconnected | Reconnect the UNO and restart the controller/service |
| Motor does not move | Switch motor power off; check separate supply, polarity, motor mapping, and loaded voltage; keep PWR jumper removed |
| Pi resets or undervoltage | Stop motor tests and correct the Pi supply/cable and motor-power routing |

For multiple USB devices, stop the existing controller and run these commands
in a Pi terminal to select the UNO explicitly:

```bash
ls -l /dev/serial/by-id/
bash ~/robotcar/current/pi/run.sh --port /dev/serial/by-id/YOUR_UNO_PORT
```

Replace the final path with the listed UNO entry. The boot service uses automatic
selection; keep other serial devices disconnected for this stage if selection
is ambiguous.

Service commands, run on the Pi:

```bash
sudo systemctl status robotcar --no-pager
sudo journalctl -u robotcar -n 40 --no-pager
sudo systemctl stop robotcar
sudo systemctl start robotcar
sudo systemctl restart robotcar
sudo systemctl disable --now robotcar
```

Stop motion and turn motor power off before maintenance. Shut Linux down cleanly
before removing Pi power.
