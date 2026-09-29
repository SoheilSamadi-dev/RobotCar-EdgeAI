# Project Components

This inventory separates hardware already tested for this project from the
contents of the ELEGOO Most Complete Starter Kit. The kit contents and quantities
are confirmed by the user's case-label photo, `docs/images/UNO-toolkit.HEIC`,
and match pages 4-9 of the downloaded English tutorial, version 1.0.2021.05.13.
The label confirms the kit configuration; it does not prove that every loose
piece is still present until the compartments are individually checked.

## Confirmed project hardware

| Component | Quantity | Status / role |
|---|---:|---|
| ELEGOO UNO R3 | 1 | Connected, programmed, and tested |
| DollaTek HW-130 L293D motor shield | 1 | M1-M4 tested individually and together |
| DollaTek acrylic four-wheel chassis | 1 | Assembled |
| Yellow geared DC motors | 4 | Tested on M1-M4 |
| Wheels | 4 | Installed; all turn forward |
| Slotted encoder discs | 4 | Installed; reader sensors not identified |
| Four-AA holder with switch | 1 | Contains four Duracell alkaline AA cells in series (6 V nominal) for shield `EXT_PWR` |
| Micro servo mounted on chassis | 1 | Visible in chassis photo; untested |
| Arduino Nicla Sense ME | 1 | User-owned; planned motion sensing |
| Raspberry Pi 3 Model B v1.2 with 32 GB microSD | 1 | Confirmed; Debian 13 cleaned for the rover and renamed `robotcar`; mobile power supply pending |

## ELEGOO kit contents shown on the user's case label

### Boards, modules, and actuators

| Component | Quantity |
|---|---:|
| ELEGOO UNO R3 controller board | 1 |
| Prototype expansion module with mini breadboard | 1 |
| Breadboard power-supply module | 1 |
| 830 tie-point breadboard | 1 |
| SG90 servo motor | 1 |
| 28BYJ-48 stepper motor | 1 |
| ULN2003 stepper-motor driver module | 1 |
| Fan blade and 3-6 V DC motor set | 1 |
| L293D motor-driver IC | 1 |
| 5 V relay | 1 |
| GY-521 motion-sensor module | 1 |
| HC-SR04 ultrasonic sensor | 1 |
| HC-SR501 PIR motion-sensor module | 1 |
| DHT11 temperature/humidity module | 1 |
| Sound-sensor module | 1 |
| Water-level sensor module | 1 |
| DS1307 real-time-clock module | 1 |
| RC522 RFID module | 1 |
| IR receiver module | 1 |
| Infrared remote control | 1 |
| Joystick module | 1 |
| Rotary-encoder module | 1 |
| 4x4 membrane keypad | 1 |
| LCD1602 module with pin header | 1 |
| MAX7219 8x8 LED matrix module | 1 |
| One-digit seven-segment display | 1 |
| Four-digit seven-segment display | 1 |
| Active buzzer | 1 |
| Passive buzzer | 1 |

### Wiring and power items

| Component | Quantity |
|---|---:|
| Breadboard jumper wires | 65 |
| Female-to-male Dupont wires | 20 |
| USB Type-A to Type-B cable | 1 |
| 9 V battery with snap-on connector clip | 1 |
| 9 V, 1 A wall adapter | 1 |

The 9 V battery and wall adapter are listed kit parts. They are not approved as
the rover's motor or Raspberry Pi supply. The chassis four-AA holder is a
separate item.

### Loose electronic components

| Component | Quantity |
|---|---:|
| 10 kOhm potentiometer | 2 |
| 74HC595 shift-register IC | 1 |
| Resistors, assorted values | 120 |
| 100 uF, 50 V electrolytic capacitors | 2 |
| 10 uF, 50 V electrolytic capacitors | 2 |
| 22 pF ceramic capacitors | 5 |
| 100 nF (`104`) ceramic capacitors | 5 |
| S8050 NPN transistors | 5 |
| PN2222 NPN transistors | 5 |
| Rectifier diodes | 5 |
| Small pushbuttons | 5 |
| Tilt-ball switch | 1 |
| Thermistor | 1 |
| Photoresistors | 2 |
| Red LEDs | 5 |
| Yellow LEDs | 5 |
| Blue LEDs | 5 |
| Green LEDs | 5 |
| White LEDs | 5 |
| RGB LEDs | 2 |

## Control options using available hardware

| Option | Wireless? | Suitable use | Project assessment |
|---|---|---|---|
| IR remote plus receiver | Yes, infrared line-of-sight | Immediate handheld direction and stop commands | Best short-term untethered test using the kit. The downloaded example uses D11, which conflicts with M1 PWM on this shield; choose a free pin and verify timer compatibility before wiring. |
| Raspberry Pi local web control | Yes, Wi-Fi | Phone/laptop control, logging, sensors, and later AI | Preferred full-project design. Pi sends commands to the UNO over USB serial. |
| Raspberry Pi Bluetooth control | Yes, Bluetooth | Phone or custom-controller input | Possible after confirming the exact Pi 3 revision and software approach; Wi-Fi web control is easier to inspect and extend. |
| Analog joystick | No, unless attached to another wireless controller | Direct speed/direction input | Useful as a wired handheld or chassis-mounted control. Analog pins appear available, but the final shield pin map must be checked. |
| 4x4 membrane keypad | No | Discrete commands and mode selection | Usable, but consumes several pins and is awkward while the car moves. |
| Pushbuttons | No | Start, stop, and emergency input | Good for a physical stop or mode button. |
| Rotary encoder | No | Speed or mode adjustment | Useful as a local setting control rather than steering. |
| RC522 RFID | Very short range | Checkpoints, mode tags, or route markers | Not suitable for continuous steering. |
| Sound sensor | Indirect | Start/stop trigger experiments | Too ambiguous for primary driving control. |
| Nicla Sense ME | Bluetooth capable | Gesture control or motion telemetry | Possible later, but the Nicla is currently planned as the rover's motion sensor. |

The UNO R3 itself has no built-in Bluetooth or Wi-Fi. The user's ELEGOO kit
label also contains no Bluetooth or Wi-Fi module.

The installed motor library uses D3, D4, D5, D6, D7, D8, D11, and D12 for the
four DC motors and shift register; D9 and D10 are reserved for the shield's
servo headers. The analog header A0-A5 and D2 appear available on this shield,
but each added module must be checked for timer and library conflicts as well as
pin availability.

## Source and verification notes

- User source: `docs/images/UNO-toolkit.HEIC` (local reference image, ignored
  from Git).
- Local vendor source: `docs/vendor/elegoo/.../English/The Most Complete Starter Kit
  for UNO V1.0.2021.05.13.pdf` (ignored from Git because it is downloaded vendor
  material).
- Public source: [ELEGOO Most Complete Starter Kit](https://eu.elegoo.com/products/elegoo-uno-most-complete-starter-kit).
- The photo confirms the exact case-label list and visibly shows the remote and
  wiring in the open case. Check the relevant compartment before selecting any
  other component for the rover.

## Latest supply clarification (2026-09-29)

The confirmed motor supply at EXT_PWR is **four Duracell alkaline AA
batteries in series**, nominally **6 V** (4 × 1.5 V). Loaded voltage remains
unmeasured. See [battery monitoring](BATTERY_MONITORING.md).
