# Motor battery monitoring design

Confirmed motor supply: **four Duracell alkaline AA batteries in series**,
connected to shield EXT_PWR. Each cell is nominally 1.5 V, giving a nominal
pack voltage of **6 V**. Actual unloaded and loaded voltage still need to be
measured; 6 V is not a replacement threshold.

The UNO cannot read this separate motor rail without a sensing circuit. Its
USB supply voltage is not the motor battery voltage. This is a proposed design,
not installed hardware or implemented telemetry.

For this four-cell pack, a divider of two 10 kΩ resistors can halve the voltage:

```text
EXT_PWR + -- 10 kΩ --+-- 10 kΩ -- EXT_PWR GND / UNO GND
                    |
                   A0
```

Confirm A0 is unused on the actual shield and verify the midpoint voltage
with a multimeter before attaching it. Never connect the battery directly to
A0. Sense the supply, not the PWM motor terminals. A 100 nF capacitor from
A0 to ground can filter noise. Keep UNO powered while the divider is connected
to the battery; disconnect the sense supply before turning UNO off to avoid
feeding an unpowered input. This divider is scoped to the four-cell pack.

Using the default ADC reference, pack voltage is approximately
`ADC * measured_UNO_5V / 1023 * 2`. Calibrate against a multimeter and account
for resistor tolerance. Average readings and report sustained low voltage and
load-induced sag separately. Measurements under load are needed before choosing warning thresholds
for this alkaline pack; voltage is not an accurate
remaining-capacity percentage.

Next implementation: optional UNO sensing → serial voltage report → Pi status
→ GUI voltage and low-battery warning. Keep it disabled until wiring and
calibration are verified.

References: [Arduino analogRead](https://github.com/arduino/reference-en/blob/master/Language/Functions/Analog%20IO/analogRead.adoc),
[Microchip ADC input guidance](https://onlinedocs.microchip.com/oxy/GUID-BB043FE0-2E9D-4920-B643-8893DEB5CC72-en-US-4/GUID-F5280497-6C4A-4F01-9B10-B327C20C9A8E.html).
