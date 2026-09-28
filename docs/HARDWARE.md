# Hardware Inventory

Status terms: **user-reported** = ownership stated; **listing evidence** = shown
in supplied product screenshots; **case-label inventory** = listed on the user's
physical ELEGOO case, but individual loose pieces may still need checking.

The detailed, publishable list is in [COMPONENTS.md](COMPONENTS.md).

| Item | Evidence | Planned role / open check |
|---|---|---|
| Arduino Nicla Sense ME | User-reported | Motion sensing; later compact inference |
| Raspberry Pi 3 Model B v1.2 with 32 GB microSD | User-confirmed | Wi-Fi control, logging, coordination, and initial inference; inspect the existing OS before changing the card |
| ELEGOO GE-EL-KIT-001 | User case-label photo: 63 component types | Most Complete/Ultimate kit; label inventory recorded in COMPONENTS.md |
| DollaTek four-wheel chassis | Listing evidence | Four geared motors and wheels; check motor specifications |
| Four-AA battery holder and switch | User-confirmed physical inventory | Motor-supply candidate; existing cells did not power the shield through `EXT_PWR` |
| Slotted encoder discs | Listing evidence | Matching electronic readers not confirmed |
| L293D IC | Case-label inventory | Separate loose motor driver; current/thermal suitability pending |
| DollaTek L293D motor drive expansion shield for UNO R3 (ASIN B07DK4NHRW) | User photo and completed tests | Identified as HW-130; M1-M4 and combined pulse tested, while motor current ratings remain unknown |
| Ultrasonic sensor and SG90 servo | Case-label inventory | Obstacle distance scan |
| GY-521 | Case-label inventory | Optional second motion sensor |
| PIR, sound, light, DHT11, thermistor, water-level sensors | Case-label inventory | Optional experiments |
| RC522 RFID reader | Case-label inventory | Optional close-range checkpoint detection |
| Joystick, buttons, IR receiver/remote, keypad, rotary encoder | Case-label inventory | Manual input and configuration |
| LCD1602, LEDs, buzzers, segment displays, MAX7219 | Case-label inventory | Status and feedback |
| 74HC595, ULN2003 board, stepper, relay, discrete parts | Case-label inventory | Supporting circuits and later mechanisms |
| Breadboard, jumpers, kit power module | Case-label inventory | Prototyping; verify ratings before use |

## Integration questions

- Four motors require an explicit driver plan. Driving left/right motor pairs on
  shared channels requires checking the combined current per channel.
- The linked DollaTek shield is separate from the loose L293D IC in the starter
  kit. Its visible labels and power arrangement were inspected and its library
  pin use recorded. Successful short tests do not establish capacity for
  sustained motor loads.
- A user photo of the shield front shows `HW-130`, four output labels `M1`–`M4`,
  an `EXT_PWR` screw terminal marked `+`/`GND`, a fitted yellow `PWR` jumper,
  and two 3-pin servo headers. The board has three socketed ICs, but the photo
  does not establish motor current capacity or the exact power-jumper circuit.
  User reports the back of the shield is empty, with no additional components
  or markings to inspect. No useful chassis motor markings were visible in the
  supplied photos.
- A user photo of the assembled chassis underside confirms four yellow plastic
  geared DC motors, four wheels, visible slotted encoder discs on the inner
  shafts, and a mounted micro servo near one end. No motor voltage, model, or
  current markings are legible in this image. No encoder reader electronics
  are visible; the discs alone cannot provide measurements.
- The Texas Instruments L293D data gives 600 mA continuous output current and
  1.2 A nonrepetitive peak current for at most 100 microseconds. The peak figure
  is not a usable allowance for an unknown motor's startup or stall current.
  With four motor outputs on this style of shield, each motor must be checked
  against its bridge rating, and total heating and supply current still matter.
  The exact motor part number and stall current have not been found in the
  downloaded ELEGOO material or the chassis references. The ELEGOO 130 motor
  datasheet describes a separate kit component, not these geared chassis motors.
- The Adafruit V1 motor shield guide documents a similar L293D shield: its
  `PWR` jumper joins the motor supply to the Arduino supply path; with separate
  USB/logic and `EXT_PWR` motor supplies, the jumper is removed. This is a
  reference design, not a verified schematic for the user's HW-130 revision.
  Do not connect motor power with the fitted jumper until the actual path is
  confirmed. Verify `EXT_PWR` polarity before any powered test.
- With the shield stacked on the UNO and USB as the only supply, the user
  confirmed that Blink still runs and the shield indicator LED lights. This
  verifies basic mechanical seating and UNO operation, but the LED does not
  establish motor supply voltage, motor outputs, or jumper behavior.
- With USB as the only supply, the user removed the yellow `PWR` shunt and
  observed that the shield indicator LED turned off. This supports the
  interpretation that the LED indicates the motor supply rail and that the
  jumper links it to the UNO supply path. It is not a complete circuit or
  polarity check.
- The saved reseller listing and the user's latest physical check agree on four
  AA cells. The earlier AAA report was corrected. Cell chemistry, loaded
  voltage, and pack current capability remain unknown; the AA holder is not
  an established Pi or four-motor supply.
- The user connected the four chassis motors using the servo end as the front:
  M1 front left, M2 rear left, M3 front right, M4 rear right. The yellow `PWR`
  shunt was installed during every successful motor test. A later controlled
  check showed that `four_motor_pulse` worked with or without cells in the AA
  holder only while this jumper was installed. This confirms that those tests
  powered the motor rail through UNO USB rather than through `EXT_PWR`. Each
  motor and shield output was tested individually with the
  wheels raised. All turned in the forward direction and stopped after a
  150 ms pulse at PWM 255. At PWM 100 for 250 ms, M1 made a sound but did not
  start, even with the wheel removed. The combined four-motor load has not
  been tested for sustained operation. A first 150 ms combined pulse at PWM
  255 moved all four motors with the chassis raised, powered through USB. The
  user confirmed
  automatic stopping, no UNO reset, no unusual heat or smell, and no very
  uneven behavior during that pulse.
- Encoder discs alone cannot provide electronic speed or distance readings.
- Use a suitable regulated supply for the Pi; keep motor transients from causing
  resets. Check total load with USB boards and the servo included.
- Verify voltage compatibility before connecting signals between the UNO, Pi,
  Nicla, and peripheral modules. Do not assume their pins tolerate the same voltage.
- Confirm chassis space, mounting, cable routing, and payload before final assembly.
- The tested motor mapping is documented. A complete Pi, Nicla, and sensor
  wiring diagram has not yet been designed.

## 2026-09-28 Pi motor test

The user reported successful motor operation through the Pi-to-UNO USB serial
link with no problems during the test. Earlier Pi undervoltage events remain
relevant: no new power measurement, motor-supply voltage, or explicit jumper
position was supplied with that confirmation. The earlier AA supply-path issue
and sustained-load checks therefore remain unresolved. See
[the Pi checkpoint](PI_SETUP.md#2026-09-28-checkpoint-motor-control-from-the-pi).

## References

- [User's ELEGOO listing](https://www.amazon.de/dp/B01IHCCKKK)
- [User's DollaTek listing](https://www.amazon.de/dp/B07F73738Z)
- [User's DollaTek L293D drive expansion shield](https://www.amazon.de/dp/B07DK4NHRW)
- [ELEGOO published inventory](https://eu.elegoo.com/de-pt/products/elegoo-uno-most-complete-starter-kit)
- [ELEGOO kit versions and tutorials](https://us.elegoo.com/blogs/arduino-projects/elegoo-uno-r3-project-the-most-complete-starter-kit-tutorial)
- [Nicla Sense ME documentation](https://docs.arduino.cc/hardware/nicla-sense-me)
- [Raspberry Pi hardware documentation](https://www.raspberrypi.com/documentation/computers/raspberry-pi.html)
- [Texas Instruments L293D specifications](https://www.ti.com/product/L293D)
- [Texas Instruments L293D datasheet](https://www.ti.com/lit/ds/symlink/l293.pdf)
- [Adafruit V1 motor shield power guide (reference design)](https://learn.adafruit.com/adafruit-motor-shield/power-requirements)

Product screenshots supplied on 2026-09-15 support identification, not a complete
physical inventory. They are not copied into this repository.
