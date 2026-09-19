# CarEdgeAI

An experimental rover that combines an Arduino Nicla Sense ME, Raspberry Pi 3,
ELEGOO UNO R3 Most Complete Starter Kit, and DollaTek four-wheel chassis to
explore AI running locally on embedded devices.

**Status:** the UNO R3, HW-130 motor shield, four-AA motor supply, and all four
chassis motors have passed raised-wheel bench tests. The repository includes
runnable Arduino sketches for individual motor pulses, a combined four-motor
pulse, and manual serial driving with an automatic stop timeout. Raspberry Pi,
Nicla sensing, data collection, and model development are the next stages.

![First assembled motor-control setup](media/first-setup.png)

## Goal

Build a manually controlled rover, collect labeled motion data, and train a small
model to recognize driving surfaces or unusual vibration. Run inference on the
Pi first and use validated predictions to adjust speed or stop. Later, explore
running a compact classifier directly on the Nicla (TinyML).

Training can happen on a development computer; the deployed robot should make
its driving decisions locally without a cloud connection.

## Proposed architecture

```mermaid
flowchart LR
    N[Nicla: motion sensing] -->|USB serial, proposed| P[Pi: logging, inference, coordination]
    P -->|USB serial, proposed| U[UNO: sensors and motor control]
    S[Ultrasonic sensor and scanning servo] --> U
    U --> D[HW-130 L293D motor shield]
    D --> M[Four chassis motors]
    P --> V[Local dashboard, later]
```

The tested manual-control sketch already enforces a 300 ms command timeout on
the UNO. Obstacle avoidance starts with distance rules; terrain recognition is
the first learned behavior. The complete Pi-to-UNO message format, final power
design, and sensor wiring remain to be chosen.

## Development milestones

1. Verify motor electrical limits and select the final power arrangement.
2. Extend the working manual drive test to an untethered controller.
3. Record labeled motion data across surfaces and separate driving sessions.
4. Compare a vibration-threshold baseline with a small learned classifier.
5. Run inference on the Pi and validate speed adaptation at low speed.
6. Explore Nicla inference, additional sensors, and a local dashboard.

## Repository guide

| Path | Purpose |
|---|---|
| [docs/HARDWARE.md](docs/HARDWARE.md) | Inventory, evidence, and unresolved checks |
| [docs/COMPONENTS.md](docs/COMPONENTS.md) | GitHub-ready component inventory and control options |
| [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) | Proposed responsibilities and AI evaluation |
| [firmware/uno/](firmware/uno/README.md) | Tested motor-control sketches and setup instructions |
| [firmware/nicla/](firmware/nicla/README.md) | Future sensing and TinyML firmware |
| [pi/](pi/README.md) | Future robot coordination and logging |
| [ml/](ml/README.md) | Future training and evaluation |

## Related work

The local Embedded-vibration-monitor project provides relevant experience with
Nicla motion sensing and a Raspberry Pi gateway. Its application thresholds,
private deployment settings, and validation results do not transfer to this rover.

## License

A license has not yet been selected. No open-source license is granted by this
repository at this stage.
