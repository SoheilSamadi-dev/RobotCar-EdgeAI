# Raspberry Pi Integration Notes

## Confirmed hardware

- Raspberry Pi 3 Model B, board revision 1.2
- 32 GB microSD card
- Micro-USB power input
- Built-in 2.4 GHz Wi-Fi and Bluetooth

The `Embedded-vibration-monitor` project used this Raspberry Pi with a 64-bit
Linux installation, SSH, Python 3, Bash, `systemd`, and `logrotate`.

An inspection on 2026-09-19 confirmed:

- Debian GNU/Linux 13 (`trixie`), 64-bit
- A 29 GB root filesystem with 5.7 GB used and 22 GB available
- Separate 512 MB FAT boot and 29.2 GB ext4 root partitions
- The old `nicla-logger` and `washer-monitor` services are still enabled
- With no USB boards connected, `nicla-logger` was activating/retrying and
  `washer-monitor` was active
- No devices were present under `/dev/serial/by-id/`

This is enough capacity for the rover software and development logs. Long-term
sensor recordings still need bounded storage or log rotation.

## Previous deployment cleanup

On 2026-09-19, the previous deployment was archived and removed from the Pi:

- The runtime directory, private configuration, installed service units, and
  log-rotation rule were saved in a checksum-verified local archive under the
  previous project's Git-ignored `archive/` directory.
- `nicla-logger` and `washer-monitor` were disabled and removed.
- Both service names then reported `not-found` and `inactive`.
- The old runtime and private-configuration directories were removed from the Pi.
- The operating system, SSH access, user account, and network configuration
  were retained.
- The root filesystem still reported 22 GB available after cleanup.

The Pi is now ready to host the rover software. Its hostname was changed from
`condition-monitor` to `robotcar`, and SSH access through `robotcar.local` was
confirmed.

## Preserve the existing installation first

Do not reimage the 32 GB card. The existing Debian installation is suitable for
the rover, and the previous deployment has already been preserved separately.

The initial read-only inspection used:

```bash
cat /proc/device-tree/model; echo
getconf LONG_BIT
cat /etc/os-release
df -h /
lsblk
systemctl --type=service --state=running
systemctl is-enabled nicla-logger washer-monitor
ls -l /dev/serial/by-id/
```

The earlier services have been removed, so they can no longer claim the Nicla
serial port when it is connected for the rover.

## Reusable lessons from Embedded-vibration-monitor

### Use stable USB device paths

Linux names such as `/dev/ttyACM0` can change when boards are unplugged or the
boot order changes. Configure the rover with the links under
`/dev/serial/by-id/` whenever the connected board provides one. Record separate
paths for the UNO and Nicla. If a board provides no unique link, add a narrow
`udev` rule after inspecting its vendor, product, and serial attributes.

### Give each serial port one owner

Only one process should read each board:

- The rover control service owns the UNO port.
- The Nicla acquisition service owns the Nicla port.
- The dashboard and analysis code consume data through the rover application,
  rather than opening either USB port independently.

This prevents a serial monitor, logger, and control process from consuming
different pieces of the same stream.

### Treat timing and gaps as data

Every Nicla message should contain device uptime, a sequence number, and units.
The Pi should add its receipt timestamp. Missing samples, device restarts, and
long gaps must be recorded explicitly instead of being interpreted as stillness
or a normal surface.

### Run tested programs as services

After interactive testing succeeds, use `systemd` to start the rover software
at boot, grant access through the `dialout` group, restart after failures, and
capture errors in the journal. Service installation comes after manual serial
and safety tests, so an unfinished program cannot move the car during boot.

### Keep deployment state outside Git

Wi-Fi credentials, host-specific USB paths, and private configuration belong in
local configuration files with restricted permissions. Source defaults and
example files can be tracked without real credentials or machine identifiers.

### Bound logs and shut down cleanly

Use log rotation or bounded structured logs so the 32 GB card cannot fill over
time. Shut down Linux and wait for it to stop before disconnecting the power
bank; abrupt removal can corrupt the microSD filesystem.

## What does not transfer directly

The washing-machine project used Nicla acceleration requested at 50 Hz, serial
at 115200 baud, raw sensor counts, one-second vibration summaries, and a tuned
threshold. Those choices were specific to one appliance and mounting position.
The rover needs acceleration and angular velocity with explicit units, enough
sample rate for surface analysis, session metadata, and new validation. Its old
thresholds and notification state machine must not be reused as rover evidence.

The UNO motor link remains at the already tested 9600 baud initially. The UNO
and Nicla are separate serial devices and do not need to use the same rate.

## Pi integration progress

Completed:

1. Retained the working Debian 13 installation and confirmed SSH access through
   `robotcar.local`.
2. Connected the UNO and found its stable `/dev/serial/by-id/` link.
3. Verified the 9600-baud UNO protocol and 300 ms motor timeout from the Pi.
4. Prototyped and tested hold-to-drive web control on the Mac.

Next:

1. Move the serial bridge and local web controller to the Pi.
2. Test browser disconnect stopping, then install the tested application as a
   boot service.
3. Connect the Nicla as a second USB device and add acquisition separately.

The target system and power arrangement are documented in
[ARCHITECTURE.md](ARCHITECTURE.md).

## 2026-09-28 checkpoint: motor control from the Pi

The user confirmed that the motor test through the Pi worked without problems.
The control path was Mac SSH session to Pi, then USB serial from Pi to UNO.
This is a user-reported functional test, not a measured endurance or power test.

During setup:

- The UNO appeared under `/dev/serial/by-id/`, pointing to `/dev/ttyACM0`.
  Use its stable by-id path for deployment; the numbered port can change.
- Debian's `python3-serial` package was already installed (3.5-2).
- The serial terminal used 9600 baud with the existing manual-control firmware.
- Wi-Fi was initially disconnected with no saved wireless profile shown by
  NetworkManager. A profile was created and automatic connection enabled.
  The user subsequently reported completing the Ethernet-disconnection check.
- Earlier power diagnostics showed undervoltage and throttling. `0x50000`
  records earlier undervoltage/throttling; `0x50005` also indicates both are
  active at the time of the reading. No post-motor-test reading was supplied.

The test instructions specified raised wheels, the yellow `PWR` jumper removed,
separate motor power at `EXT_PWR`, and a short movement command. The final
confirmation did not independently document the physical power arrangement,
each direction, stop timing, or disconnect behavior. Keep those checks open.
The earlier four-AA supply issue is not considered resolved by this report.

### Repeat the serial connection check

With motor power off and the UNO connected to the Pi by USB:

```bash
ls -l /dev/serial/by-id/
python3 -m serial.tools.miniterm /dev/serial/by-id/YOUR_UNO_PORT 9600
```

Replace `YOUR_UNO_PORT` with the actual listed device name. Wait for the UNO to
start, then send `h`, `?`, and `x` to check help, stopped status, and explicit
stop. Exit miniterm with Ctrl+]. Close it before starting another serial owner.
The manual-control sketch releases motors after 300 ms without another motion
command; verify that behavior on hardware before continuous GUI control.

### Next milestone: reuse the existing web GUI on the Pi

Reuse `tools/mac_web_controller.py` and `tools/web/`; do not build a second UI.
The current server binds to `127.0.0.1`, so it is not yet directly reachable
from another device over Wi-Fi.

1. Adapt the controller for Pi deployment: Linux stable serial paths, explicit
   serial-port selection, headless startup, and configurable listen address.
2. Install its dependencies in a Pi virtual environment and transfer the
   controller and web assets. Keep Wi-Fi credentials and device-specific
   settings outside Git.
3. Connect the existing browser UI to the Pi-hosted server on the local network;
   retain the current Mac workflow and avoid public internet exposure.
4. Preserve the 100 ms movement heartbeat and independent UNO 300 ms timeout.
   Verify release, explicit stop, tab close, Wi-Fi loss, server termination,
   and USB disconnect with wheels raised. Check competing browser clients.
5. Record power readings before and during the test and confirm the motor
   supply is separate from Pi/UNO USB power.
6. Only after interactive validation, install the controller as a boot service
   that starts with motors stopped and has sole ownership of the serial port.

No Pi web-controller deployment or service installation was performed at this
checkpoint. Motor ratings, sustained-load behavior, and power reliability remain
open hardware checks.

## 2026-09-29: Pi web-controller implementation ready

Added Linux serial discovery, configurable local-network binding, a headless
launcher, and a runtime-only deployment helper. The existing GUI now uses
expiring control tokens and ordered commands so one browser owns movement;
release and connection gaps invalidate that control. The UNO firmware is
unchanged. See [the Pi guide](../pi/README.md) for deployment and test steps.

Local software verification uses a fake UNO and browser-event tests. Actual Pi
deployment and motor-powered browser tests are not yet confirmed: key-based
SSH authentication was unavailable during implementation, so deployment is
prepared for the user to run with their password entered locally. No boot
service has been enabled and no physical movement was commanded by these tests.
