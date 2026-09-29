# Build and drive the rover

This guide gets the current UNO firmware and Pi-hosted browser controller running.
The documented deployment route uses a Mac with a terminal, Git, SSH, and Arduino
IDE. The Pi runtime requires Python 3.10 or newer, pyserial, and Bash; automatic
startup also requires systemd. The project has used a Pi 3 Model B with 64-bit
Debian 13. Other OS and development-computer combinations are not verified here.

Use a trusted local network. The controller has no login; any device that can
reach it can request control or stop the rover. Do not expose port 8765 to the
internet.

## 1. Download the project

On your development computer:

```bash
git clone https://github.com/SoheilSamadi-dev/RobotCar-EdgeAI.git
cd RobotCar-EdgeAI
```

Keep this project folder available for the remaining computer-side commands.
Install Arduino IDE if needed. Python and Node.js on this computer are only
needed for optional direct USB use or development tests.

## 2. Assemble and check the hardware

Follow [hardware and wiring](HARDWARE.md) for the required parts, motor mapping,
and separate power connections. Keep all power disconnected while wiring.
Define the servo end of the reference chassis as the front, even if you leave
its servo unconnected.

Before continuing, confirm M1/M2 are the left motors, M3/M4 are the right
motors, the shield's yellow `PWR` jumper is removed, and the motor supply goes
to `EXT_PWR` with the correct polarity. Leave motor power OFF and raise the
wheels so they cannot touch the bench.

## 3. Upload the UNO firmware

1. Connect the UNO to your development computer with a USB data cable.
2. In Arduino IDE, install **Arduino AVR Boards** through Boards Manager.
3. Through Library Manager, install **Adafruit Motor Shield R4 Compatible**.
   The sketch needs `AFMotor_R4.h`; the Motor Shield V2 library is not compatible.
4. Open `firmware/uno/manual_serial_control/manual_serial_control.ino`.
5. Select **Arduino Uno** and the UNO's port, then upload the sketch.
6. Open Serial Monitor at **9600 baud**. Send `?`. Confirm a configuration line
   with `protocol=2`, `speed=195`, `curve=75`, `min=195`, and `max=255`.
   Send `x` to stop. Motor power stays off for this check.
7. Close Serial Monitor and disconnect UNO USB from the computer.

Use only this sketch for browser control; there is no prerequisite pulse-test
program to upload.

## 4. Prepare the Pi

Follow [Pi preparation](PI_SETUP.md) to configure an OS, SSH, local Wi-Fi,
Python, pyserial, and serial permissions. Return here when the prerequisite
checks pass and SSH works over Wi-Fi without an Ethernet cable.

Examples use `YOUR_USER@robotcar.local`. Replace `YOUR_USER` with your Pi login
and `robotcar.local` with your Pi hostname or local IP address everywhere,
including browser URLs. Passwords are entered at SSH prompts, never in files.

Connect the UNO to the Pi by USB. Power the Pi from its own suitable supply;
leave the motor battery switched OFF.

## 5. Deploy and start the controller

From the cloned project folder on your development computer:

```bash
bash pi/deploy.sh YOUR_USER@robotcar.local
ssh -t YOUR_USER@robotcar.local 'bash ~/robotcar/current/pi/run.sh'
```

The deployment command copies only runtime files. The second command starts
the server in the foreground; keep that terminal open. Open
`http://robotcar.local:8765` from a browser on the same network.

**Checkpoint:** the page reports the UNO connected and shows drive PWM **195**
and curve strength **75%**. If it reports incompatible firmware, repeat step 3
with the sketch from this same checkout. If there is no connection, use
[troubleshooting](../pi/README.md#troubleshooting) before enabling motor power.

## 6. Test with the wheels raised

1. With motor power still off, confirm the page responds and stop commands
   appear in its messages.
2. Check the separate supply and polarity, then enable motor power. The motors
   should remain stopped until you press a movement control.
3. Briefly hold **W / Forward**, then release. All wheels should move forward
   and stop on release. If a wheel runs backward, switch motor power off,
   disconnect power, and reverse that motor's two wires at its shield output.
4. Test **S** (reverse), **A/D** (pivot), and **Q/E/Z/C** (curves). **X** or
   **Space** stops all motion. On-screen direction buttons also work.
5. Check stopping when the browser loses focus or closes, Wi-Fi drops, the
   server is terminated, and the UNO USB cable is removed. Re-establish the
   connection and restart the server as needed between checks. Motion must
   require a fresh press after recovery.
6. Open a second browser. It must not take control while the first is driving;
   its explicit stop must still work.
7. Check loaded supply voltage, resets, and motor/driver heating. Record the
   results for your build. Stop immediately if motion or power is unreliable.

The firmware releases motors after a 300 ms command gap; this is not active
braking or a guaranteed physical stopping distance. PWM is motor duty, not
measured speed. A lower inner-wheel PWM during curves can stall a loaded motor.

The project's reported successful driving test does not establish every failure
case above. Do not proceed to floor driving until your raised-wheel checks and
power checks pass. Start with short movements in a clear area, with the motor
power switch accessible.

## 7. Finish or enable automatic startup

For foreground operation, stop the rover, turn motor power OFF, and press
Ctrl+C in the server terminal. Closing a browser alone does not shut down the Pi.
Shut the Pi down cleanly before removing its supply:

```bash
ssh -t YOUR_USER@robotcar.local 'sudo shutdown -h now'
```

Wait for shutdown to complete before disconnecting power.

Once manual operation passes, optionally follow
[automatic startup](../pi/README.md#automatic-startup). Its installer is
implemented, but its first installation and reboot check still need hardware
confirmation. Foreground operation is sufficient to reproduce the current
reported working milestone.
