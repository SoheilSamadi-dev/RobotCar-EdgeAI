# Prepare the Raspberry Pi

Return to the [setup guide](GETTING_STARTED.md#5-deploy-and-start-the-controller)
after completing these steps.

## Operating system and network

Use a working Linux installation with Python 3.10+, Bash, SSH, and systemd.
The reference setup is a Pi 3 Model B with a 32 GB microSD and 64-bit Debian 13.
An existing compatible installation can be retained; no earlier project or
service is required.

For a blank card, use Raspberry Pi Imager on your computer to install a
Pi-3-compatible 64-bit OS. Writing an image erases the selected card. Configure
a normal user account, hostname (the examples use `robotcar`), SSH access, and
your local Wi-Fi credentials before booting. The Pi 3 Model B needs a 2.4 GHz
Wi-Fi network. If your imaging workflow does not configure these settings,
complete them with a keyboard and display on the Pi before continuing.

Boot with a suitable Pi supply, then connect from your computer:

```bash
ssh YOUR_USER@robotcar.local
```

Replace the example account and host. If hostname lookup fails, find the Pi's
address in your router's client list and use that address instead. Confirm SSH
works on Wi-Fi with Ethernet unplugged, including after a reboot. The browser
device must be able to reach the Pi; guest-network isolation can prevent this.

## Install runtime dependencies

Run these commands **in the Pi SSH session** on a Debian-based OS:

```bash
sudo apt update
sudo apt install python3 python3-serial
python3 --version
python3 -c 'import sys, serial; assert sys.version_info >= (3, 10); print("Python and pyserial ready")'
sudo usermod -aG dialout "$USER"
```

Log out and reconnect for group membership to take effect. Keep motor power
off, attach the UNO by USB, and check:

```bash
id -nG
ls -l /dev/serial/by-id/
```

Your groups should include `dialout`. The device list should contain the UNO.
If it does not, check the USB data cable and `ls -l /dev/ttyACM* /dev/ttyUSB*`.
The controller prefers stable by-id paths and refuses ambiguous selection.
See [explicit port selection](../pi/README.md#troubleshooting) if needed.

Close serial monitors and other programs using the UNO port before launching
the controller. Run it as the normal user, not root. No Node.js or Arduino IDE
is required on the Pi.

## Power check

Use the [separate power arrangement](HARDWARE.md#power-and-wiring). Verify a
stable Pi supply and check for undervoltage or resets while the UNO is attached
and during your raised-wheel motor tests. If your OS provides `vcgencmd`,
`vcgencmd get_throttled` can help inspect power/throttling flags. Power reliability
and sustained motor load have not been fully validated for the reference build.
