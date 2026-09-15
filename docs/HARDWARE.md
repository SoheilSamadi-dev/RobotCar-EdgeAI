# Hardware Inventory

Status terms: **user-reported** = ownership stated; **listing evidence** = shown
in supplied product screenshots; **published inventory** = expected kit contents,
not yet checked against the physical box.

| Item | Evidence | Planned role / open check |
|---|---|---|
| Arduino Nicla Sense ME | User-reported | Motion sensing; later compact inference |
| Raspberry Pi 3 | User-reported | Logging, coordination, initial inference; confirm revision |
| ELEGOO GE-EL-KIT-001 | Listing evidence: 63 component types | Most Complete/Ultimate kit; audit actual contents |
| DollaTek four-wheel chassis | Listing evidence | Four geared motors and wheels; check motor specifications |
| Four-AA holder and switch | Listing evidence | Motor supply candidate; cells and power design pending |
| Slotted encoder discs | Listing evidence | Matching electronic readers not confirmed |
| L293D IC | Published inventory | Motor driver candidate; current/thermal suitability pending |
| Ultrasonic sensor and SG90 servo | Published inventory | Obstacle distance scan |
| GY-521 | Published inventory | Optional second motion sensor |
| PIR, sound, light, DHT11, thermistor, water-level sensors | Published inventory | Optional experiments |
| RC522 RFID reader | Published inventory | Optional close-range checkpoint detection |
| Joystick, buttons, IR receiver/remote, keypad, rotary encoder | Published inventory | Manual input and configuration |
| LCD1602, LEDs, buzzers, segment displays, MAX7219 | Published inventory | Status and feedback |
| 74HC595, ULN2003 board, stepper, relay, discrete parts | Published inventory | Supporting circuits and later mechanisms |
| Breadboard, jumpers, kit power module | Published inventory | Prototyping; verify ratings before use |

## Integration questions

- Four motors require an explicit driver plan. Driving left/right motor pairs on
  shared channels requires checking the combined current per channel.
- Encoder discs alone cannot provide electronic speed or distance readings.
- Use a suitable regulated supply for the Pi; keep motor transients from causing
  resets. Check total load with USB boards and the servo included.
- Verify voltage compatibility before connecting signals between the UNO, Pi,
  Nicla, and peripheral modules. Do not assume their pins tolerate the same voltage.
- Confirm chassis space, mounting, cable routing, and payload before final assembly.
- No pinout or wiring diagram has been approved at this stage.

## References

- [User's ELEGOO listing](https://www.amazon.de/dp/B01IHCCKKK)
- [User's DollaTek listing](https://www.amazon.de/dp/B07F73738Z)
- [ELEGOO published inventory](https://eu.elegoo.com/de-pt/products/elegoo-uno-most-complete-starter-kit)
- [ELEGOO kit versions and tutorials](https://us.elegoo.com/blogs/arduino-projects/elegoo-uno-r3-project-the-most-complete-starter-kit-tutorial)
- [Nicla Sense ME documentation](https://docs.arduino.cc/hardware/nicla-sense-me)
- [Raspberry Pi hardware documentation](https://www.raspberrypi.com/documentation/computers/raspberry-pi.html)

Product screenshots supplied on 2026-09-15 support identification, not a complete
physical inventory. They are not copied into this repository.
