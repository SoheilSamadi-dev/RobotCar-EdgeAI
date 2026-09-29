# UNO motor-control firmware

Upload [manual_serial_control.ino](manual_serial_control/manual_serial_control.ino)
for the current rover. This is the only required sketch. Follow the
[setup guide](../../docs/GETTING_STARTED.md#3-upload-the-uno-firmware) for library
installation, board selection, upload, and initial checks.

The sketch starts stopped and releases all motors after 300 ms without a
movement command. The Pi web controller supplies repeated commands while a
control is held.

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
| `+` / `-` | Raise / lower PWM speed by 5 |
| `1` through `9` | Select PWM 195–255; `9` is full power |
| `?` | Print motion, speed, and protocol-2 configuration |
| `H` | Print the command list |

Movement commands are case-insensitive. A Mac or Pi keyboard controller must
repeat the active movement command more frequently than every 300 ms. Releasing
the key must send a stop command. This heartbeat behavior makes the UNO stop if
the controller program, USB connection, or network connection fails.

The Arduino IDE Serial Monitor can send individual commands for bench checks,
but it does not provide real-time key-down and key-up events. The
[shared web controller](../../tools/web_controller.py) provides
hold-to-drive control and sends the required heartbeat.

## PWM and curve settings

Default and minimum drive PWM are 195; maximum is 255. Levels 1–9 select
195, 202, 210, 217, 225, 232, 240, 247, and 255. This is motor duty, not measured
vehicle speed. Stop still releases all motors.

Send `@c75` followed by newline to set curve strength to 75 percent. Accepted
values are integers 0–100. Inner PWM is `base * (100 - strength) / 100`, with
integer truncation. At 0 both sides match; 50 halves the inner PWM; at 100
the inside motors are released. Default is 75. The reduced inside PWM may be
below 195 and may stall under load; the base minimum applies to the outside
wheels. Grip and load determine actual radius. Settings reset on UNO restart.

Configuration commands do not refresh the movement timeout. Malformed or
incomplete frames stop motion. The web controller requires a protocol-2
configuration response before permitting movement, so upload this sketch
before using the updated GUI.
