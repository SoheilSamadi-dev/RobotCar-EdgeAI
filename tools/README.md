# Shared web controller

[web_controller.py](web_controller.py) is the active server for the Pi and
optional direct USB operation on a Mac. Browser assets live in `web/` and the
runtime dependency is listed in `requirements-web.txt`.

For the normal Pi/Wi-Fi build, use the [setup guide](../docs/GETTING_STARTED.md).
No separate Mac controller is required.

## Optional direct USB operation

This can help diagnose the UNO without the Pi. With Python 3.10+ on the Mac,
run from the project root:

```bash
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install -r tools/requirements-web.txt
python3 tools/web_controller.py
```

First upload the current UNO sketch, close Serial Monitor, and connect the UNO
directly to the Mac. Keep motor power off until the page reports connected and
the expected configuration. Use the same wiring and raised-wheel checks as the
setup guide. The server opens `http://127.0.0.1:8765` and defaults to loopback.

If automatic serial selection is ambiguous, add `--port` followed by your
actual UNO device path. Use `--help` to list options. Ctrl+C stops the controller
and releases the serial port. Turn motor power off after use.
