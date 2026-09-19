# Proposed Architecture

## Responsibilities

- **UNO:** motor outputs, peripheral acquisition, command validation, startup-off
  behavior, and a command watchdog that stops motion if the Pi stops communicating.
- **Nicla:** timestamped accelerometer/gyroscope samples with explicit units and
  sequence numbers; compact inference is a later experiment.
- **Pi:** serial connections, recording, manual commands, model inference, and
  behavior coordination. A local Wi-Fi dashboard is the preferred untethered
  controller after the data path works.
- **Development computer:** dataset review, model training, and offline evaluation.

USB serial at 9600 baud is working between the development computer and UNO for
manual commands. The Pi-to-UNO protocol, Nicla baud and sample rates, device
identification, and full message schemas remain to be chosen.

The kit IR remote and receiver provide a useful interim handheld controller.
They require line of sight and careful pin/timer selection around the motor
shield. The Pi remains the long-term controller because it can provide local
Wi-Fi control, logging, coordination, and model inference together.

## First AI experiment

Classify short motion windows into a small set of observed surface classes.
Include commanded speed in the experiment design because vibration changes with
speed as well as surface. Begin with statistical motion features and a small
classifier; compare it with a simple threshold baseline before choosing a model.

Split recordings by driving session before windowing to avoid nearly identical
overlapping data entering both training and evaluation. Record class confusion,
latency, memory, and behavior on unseen conditions. Define confidence handling;
uncertain predictions must not be treated as reliable terrain identification.

First run in observation-only mode. Add bounded speed adaptation only after
held-out tests and low-speed trials support it. Distance-based obstacle stopping
and the command watchdog remain independent of learned predictions.

## Initial data plan

Record session ID, sensor timestamp, host receipt time, sample sequence, units,
acceleration, angular velocity, commanded speed, and surface label. Record
mounting, battery conditions, and sample gaps in session metadata. Actual wheel
speed is unavailable until encoder feedback is implemented and verified.

Keep raw data under ignored data/raw/ or recordings/. Commit small reviewed
examples and model metadata deliberately. Large model binaries belong in a
separately chosen release/storage workflow.

## Scope

The first version does not require a camera, cloud AI, autonomous mapping, or
reinforcement learning. No accuracy or real-time performance target has yet been
validated. Nicla sensor-hub capabilities do not automatically run our custom model;
deployment support and memory must be checked for the chosen implementation.
