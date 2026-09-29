# Development checks

These checks use a fake UNO, browser-event simulation, and a small Arduino shim.
They do not open real serial hardware and do not replace a firmware build in
Arduino IDE or physical motion/power tests.

From the repository root, with Python 3.10+, Node.js, and a C++17 compiler:

```bash
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install -r tools/requirements-web.txt
python3 -m unittest discover -s tests -p 'test_*.py' -v
node tests/test_web_client.cjs
c++ -std=c++17 -I tests/arduino_stub tests/test_firmware.cpp -o /tmp/robotcar-firmware-test
/tmp/robotcar-firmware-test
bash -n pi/deploy.sh
bash -n pi/run.sh
bash -n pi/install-service.sh
```

Python HTTP tests need permission to bind a temporary loopback port. Browser
tests run in Node without a real browser. Firmware tests cover PWM limits,
curves, malformed framing, stop, and watchdog behavior using the actual sketch.
