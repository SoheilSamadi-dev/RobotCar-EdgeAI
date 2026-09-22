# UNO Firmware

The UNO is the motor-control and immediate-stop layer in the agreed
[target architecture](../../docs/ARCHITECTURE.md).

The first bench sketch, [one_motor_pulse](one_motor_pulse/one_motor_pulse.ino),
targets the L293D/74HC595 V1-style shield layout. It keeps the selected motor
output released until the USB serial monitor sends `p`, then runs that output
forward at PWM 255 for 150 ms and releases it. `kMotorPort` is currently set
to 4, matching the last individual output tested. It uses the installed
**Adafruit Motor Shield R4 Compatible**
library, whose `AFMotor_R4.h` API targets the V1-style shield layout. The user
confirmed all four motors and all four outputs work individually with wheels
raised.

The [four_motor_pulse](four_motor_pulse/four_motor_pulse.ino) bench sketch
keeps M1–M4 released until the USB serial monitor sends `p`. It then drives all
four outputs forward at PWM 255 for 150 ms and releases every output. The
raised-wheel combined test passed: all four motors moved, stopped automatically,
and caused no observed UNO reset, unusual heat, smell, or large speed mismatch.

The [manual_serial_control](manual_serial_control/manual_serial_control.ino)
sketch provides a keyboard-ready command protocol over USB serial. It starts
with all motors released, stops on an unknown command, and releases every motor
after 300 ms without a new motion command. Repeated motion commands are required
for continuous movement. Forward, backward, pivoting, curved movement, speed
commands, stop-on-release, and the browser heartbeat were tested through the
Mac web controller with the wheels raised.

### Manual-control commands

| Key | Action |
|---|---|
| `W` or `F` | Forward |
| `S` or `B` | Backward |
| `A` or `L` | Pivot left in place |
| `D` or `R` | Pivot right in place |
| `Q` / `E` | Curve forward left / right |
| `Z` / `C` | Curve backward left / right |
| `X`, space, or `0` | Stop and release all motors |
| `+` / `-` | Raise / lower PWM speed by 15 |
| `1` through `9` | Select a speed level; `9` is full power |
| `?` | Print current motion and speed |
| `H` | Print the command list |

Movement commands are case-insensitive. A Mac or Pi keyboard controller must
repeat the active movement command more frequently than every 300 ms. Releasing
the key must send a stop command. This heartbeat behavior makes the UNO stop if
the controller program, USB connection, or network connection fails.

The Arduino IDE Serial Monitor can send individual commands for bench checks,
but it does not provide real-time key-down and key-up events. The
[Mac web controller](../../tools/mac_web_controller.py) provides
hold-to-drive control and sends the required heartbeat.

## Build and upload

1. Install the Arduino IDE and its **Arduino AVR Boards** support.
2. Install **Adafruit Motor Shield R4 Compatible** from Library Manager. These
   sketches use `AFMotor_R4.h`; the Adafruit Motor Shield V2 library controls a
   different shield design.
3. Select **Arduino Uno** and the serial port that appears when the UNO is
   connected.
4. Keep the shield's yellow `PWR` jumper removed. Power the UNO through USB.
   For a powered motor test, connect a verified separate motor battery to
   `EXT_PWR`, observing its `+` and `GND` labels. The existing four-AA path has
   not yet powered the shield successfully.
5. Raise the wheels before uploading or sending a motion command. Open Serial
   Monitor at **9600 baud** for all three sketches.

Motor mapping, with the servo end of the chassis treated as the front:

| Shield output | Motor position |
|---|---|
| M1 | Front left |
| M2 | Rear left |
| M3 | Front right |
| M4 | Rear right |

Future rover firmware will accept commands from the Raspberry Pi and add
peripheral readings. Confirm the unknown motor ratings and final power design
before sustained or loaded driving.
