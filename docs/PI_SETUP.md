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
