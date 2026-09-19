# UNO Firmware

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
sketch adds `f`, `b`, `l`, `r`, and `s` commands over USB serial. It starts with
all motors released, stops on an unknown command, and releases every motor
after 300 ms without a new motion command. Repeated commands are required for
continuous movement. Raised-wheel forward, backward, left-pivot, right-pivot,
and stop control have been confirmed.

## Build and upload

1. Install the Arduino IDE and its **Arduino AVR Boards** support.
2. Install **Adafruit Motor Shield R4 Compatible** from Library Manager. These
   sketches use `AFMotor_R4.h`; the Adafruit Motor Shield V2 library controls a
   different shield design.
3. Select **Arduino Uno** and the serial port that appears when the UNO is
   connected.
4. Keep the shield's yellow `PWR` jumper removed. Power the UNO through USB and
   connect the switched four-AA holder to `EXT_PWR`, observing its `+` and
   `GND` labels.
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
