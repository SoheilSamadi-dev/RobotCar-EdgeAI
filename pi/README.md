# Raspberry Pi Application

The Raspberry Pi is the rover's networked coordinator. It will host the local
phone-friendly control page, send a continuing motor-command stream to the UNO,
record Nicla measurements and rover status, and run the first AI models. The
complete system and power design is documented in
[docs/ARCHITECTURE.md](../docs/ARCHITECTURE.md).
The confirmed Pi hardware, safe inspection steps, and reusable lessons from the
earlier vibration-monitor project are in
[docs/PI_SETUP.md](../docs/PI_SETUP.md).

The first Pi application will provide:

1. Stable identification and connection of the UNO USB serial device.
2. Repeated movement commands plus `x` for stop using the proven 9600-baud
   bench protocol.
3. An immediate `x` command when the web client releases a control, disconnects,
   or reports an error.
4. A local web interface with hold-to-drive controls and visible connection
   state.
5. Structured logs for commands, UNO responses, stop reasons, and timestamps.

The UNO remains responsible for the 300 ms motor timeout. The Pi application
must treat that timeout as a second safety layer rather than its normal stopping
method.

No Pi application or dependency definition exists yet. Keep Wi-Fi credentials,
host-specific device names, and other machine settings outside tracked files.
