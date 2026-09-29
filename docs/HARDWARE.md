# Hardware and wiring

This list covers the current browser-controlled rover. Nicla, ultrasonic sensors,
servo control, encoders, and other starter-kit parts are not needed or supported
by the current control firmware.

## Parts

| Part | Reference setup / requirement |
|---|---|
| Raspberry Pi | Pi 3 Model B v1.2 with Wi-Fi |
| microSD | 32 GB in the reference build; compatible Linux installation |
| Pi power | Regulated 5 V supply suitable for Pi 3, rated at least 2.5 A, with a suitable Micro-USB cable; a power bank can support untethered use |
| Motor controller | ELEGOO UNO R3 / Arduino Uno-compatible board |
| Motor shield | HW-130 L293D/74HC595 V1-style shield with M1–M4 and EXT_PWR; not the Adafruit V2 shield |
| Chassis | DollaTek four-wheel chassis with four geared DC motors |
| Motor supply | Switched four-AA holder with four alkaline AA cells in series, 6 V nominal; suitability under load must be checked |
| USB cable | Data-capable cable from Pi/computer to UNO |
| Setup equipment | Computer with Arduino IDE, screwdriver, and multimeter for polarity and voltage checks |
| Browser device | Phone or computer on the same trusted local network |

You do not need the entire ELEGOO starter kit to reproduce this stage.
Motor ratings for the reference chassis remain unknown. A short successful
motion test does not establish driver current margin, loaded battery voltage,
or sustained runtime. Verify your motors and supply before extended operation.

## Power and wiring

Disconnect all power before fitting the shield or changing wiring.

1. Fit the HW-130 shield onto the UNO, checking header alignment.
2. Remove the shield's yellow `PWR` jumper and leave it removed.
3. Connect each motor to its own shield output using the table below.
4. Connect the switched motor battery to `EXT_PWR`: battery positive to `+`,
   battery negative to `GND`. Check terminal labels and polarity with a meter.
5. Power the Pi through Micro-USB from its separate supply.
6. Connect Pi USB to UNO USB for logic power and serial communication.

```text
Pi supply -- Micro-USB --> Pi -- USB data + logic power --> UNO + shield
Motor battery + --------> shield EXT_PWR +
Motor battery - --------> shield EXT_PWR GND
                          PWR jumper REMOVED
Shield M1, M2, M3, M4 ---> one motor per output
```

The motor battery must power the motors independently of Pi/UNO USB power.
If motors only work with the jumper fitted, stop and diagnose the separate
supply; do not use the jumper to bypass a failed motor-power path. The 6 V pack
rating is nominal, not a measured loaded voltage or a proven suitability rating.

## Motor mapping

Choose the end with the reference chassis's servo mount as the front. The servo
can remain electrically disconnected.

| Output | Motor position, viewed in the forward direction |
|---|---|
| M1 | Front left |
| M2 | Rear left |
| M3 | Front right |
| M4 | Rear right |

Secure the boards and battery, insulate exposed contacts, and keep cables away
from wheels. Raise the wheels for first use. Verify each wheel's direction with
the current firmware; reverse a motor's two leads with power disconnected if
needed. Follow the [setup guide](GETTING_STARTED.md) for upload and motion tests.

## Limits to verify on your build

- Motor startup/stall current versus the actual driver's ratings and cooling.
- Battery voltage under load, correct separate-supply operation, and Pi stability.
- Stopping on release and connection failure; motor release is not active braking.
- Secure mounting and acceptable motor/driver temperature during longer runs.

The reference build has reported working browser control, but these electrical
and sustained-operation checks are not all documented as complete.
