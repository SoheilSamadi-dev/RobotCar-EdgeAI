#!/usr/bin/env python3
"""Serve the RobotCar keyboard UI and forward commands to an UNO over USB."""

from __future__ import annotations

import argparse
import glob
import json
import re
import secrets
import signal
import threading
import time
import webbrowser
from collections import deque
from http import HTTPStatus
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

try:
    import serial
except ImportError:
    raise SystemExit(
        "pyserial is missing. Run: "
        "python3 -m pip install -r tools/requirements-web.txt"
    )


BAUD_RATE = 9600
DEFAULT_WEB_PORT = 8765
ALLOWED_COMMANDS = frozenset("wasdqezcxfb lr+-=1234567890?h")
MOVEMENT_COMMANDS = frozenset("wasdqezcfblr")
WEB_ROOT = Path(__file__).resolve().parent / "web"
PORT_PATTERNS = ("/dev/cu.usbmodem*", "/dev/cu.usbserial*")
CONTROL_TIMEOUT = 0.30



def normalize_command(command):
    if not isinstance(command, str):
        raise ValueError("Command must be text")
    command = command.lower()
    if ((len(command) == 1 and command in ALLOWED_COMMANDS) or
            re.fullmatch(r"@c(?:0|[1-9][0-9]?|100)", command)):
        return command
    raise ValueError("Unsupported command")


class EventLog:
    def __init__(self, maximum: int = 250) -> None:
        self._events: deque[dict[str, object]] = deque(maxlen=maximum)
        self._sequence = 0
        self._lock = threading.Lock()

    def add(self, level: str, message: str) -> None:
        with self._lock:
            self._sequence += 1
            self._events.append(
                {
                    "id": self._sequence,
                    "level": level,
                    "message": message,
                    "time": time.strftime("%H:%M:%S"),
                }
            )
        print(f"[{level.upper()}] {message}")

    def after(self, sequence: int) -> list[dict[str, object]]:
        with self._lock:
            return [event for event in self._events if event["id"] > sequence]


def find_uno_port() -> str:
    # Prefer stable Linux names; never open every port to discover a board.
    linux = sorted(glob.glob("/dev/serial/by-id/*"))
    patterns = (*PORT_PATTERNS, "/dev/ttyACM*", "/dev/ttyUSB*")
    matches = linux or sorted(
        {
            path
            for pattern in patterns
            for path in glob.glob(pattern)
        }
    )
    if not matches:
        raise RuntimeError(
            "No UNO serial port found. Connect it by USB and close Serial Monitor."
        )
    if len(matches) > 1:
        choices = ", ".join(matches)
        raise RuntimeError(
            f"Multiple serial ports found: {choices}. Select one with --port."
        )
    return matches[0]


class UnoBridge:
    def __init__(self, port: str, events: EventLog) -> None:
        self.port = port
        self.events = events
        self._serial = serial.Serial(port, BAUD_RATE, timeout=0.1, write_timeout=0.2, exclusive=True)
        self._write_lock = threading.RLock()
        self._stop_event = threading.Event()
        self._reader: threading.Thread | None = None
        self._last_motion: str | None = None
        self._healthy = True
        self.configuration = None

    def start(self) -> None:
        self.events.add("info", "Waiting two seconds for the UNO to restart")
        time.sleep(2)
        self._serial.reset_input_buffer()
        self._reader = threading.Thread(target=self._read_loop, daemon=True)
        self._reader.start()
        self.send("x")
        self.send("?")
        self.events.add("success", f"UNO connected on {self.port}")

    @property
    def connected(self) -> bool:
        return self._healthy and self._serial.is_open

    def send(self, command: str) -> None:
        command = normalize_command(command)

        try:
            with self._write_lock:
                if not self.connected:
                    raise serial.SerialException("UNO disconnected; restart the controller")
                self._serial.write((command + ("\n" if command.startswith("@") else "")).encode("ascii"))
                # Avoid an unbounded drain call after USB removal.
                # write_timeout bounds the write; the UNO owns the final watchdog.
        except serial.SerialException as exc:
            self._healthy = False
            self.events.add("error", f"Serial write failed: {exc}")
            raise

        # Do not fill the event window with 100 ms heartbeat repetitions.
        if command in MOVEMENT_COMMANDS:
            if command != self._last_motion:
                self.events.add("command", f"Movement command: {command.upper()}")
            self._last_motion = command
        elif command in {"x", " "}:
            if self._last_motion is not None:
                self.events.add("command", "Stop command")
            self._last_motion = None
        else:
            self.events.add("command", f"Command: {command.upper()}")

    def _read_loop(self) -> None:
        while not self._stop_event.is_set():
            try:
                line = self._serial.readline()
            except serial.SerialException as exc:
                self._healthy = False
                self.events.add("error", f"UNO connection lost: {exc}")
                return
            if line:
                message = line.decode("utf-8", errors="replace").strip()
                if message:
                    self.read_configuration(message)
                    level = "warning" if "TIMEOUT" in message else "uno"
                    self.events.add(level, f"UNO: {message}")

    @property
    def firmware_ready(self):
        return bool(self.configuration and self.configuration["protocol"] == 2)

    def read_configuration(self, message):
        if message.startswith("ROBOTCAR READY"):
            self.configuration = None
        match = re.fullmatch(
            r"CONFIG: protocol=2 speed=(\d+) curve=(\d+) min=195 max=255", message)
        if match:
            speed, curve = map(int, match.groups())
            if 195 <= speed <= 255 and 0 <= curve <= 100:
                self.configuration = {"protocol": 2, "speed": speed, "curve": curve,
                                      "minimum": 195, "maximum": 255}

    def close(self) -> None:
        with self._write_lock:
            try:
                if self.connected:
                    self.send("x")
            except (serial.SerialException, ValueError):
                pass
            self._healthy = False  # Reject any request racing with shutdown.
        self._stop_event.set()
        if self._reader is not None:
            self._reader.join(timeout=0.3)
        if self._serial.is_open:
            self._serial.close()
        self.events.add("info", "Serial connection closed")


class ControlConflict(ValueError):
    pass


class ControlSession:
    """One short-lived controller lease; never repeat a motion on the server."""

    def __init__(self, bridge, clock=time.monotonic):
        self.bridge = bridge
        self.clock = clock
        self.lock = threading.RLock()
        self.token = None
        self.sequence = -1
        self.deadline = 0.0

    def _stop(self):
        self.token = None  # Invalidate before USB I/O, even if it fails.
        self.sequence = -1
        self.bridge.send("x")

    def expire(self):
        with self.lock:
            if self.token is not None and self.clock() >= self.deadline:
                self._stop()

    def acquire(self):
        with self.lock:
            self.expire()
            if not self.bridge.connected:
                raise serial.SerialException("UNO disconnected")
            if not self.bridge.firmware_ready:
                raise ControlConflict("Upload the updated UNO firmware, then restart the controller")
            if self.token is not None:
                raise ControlConflict("Another control is active; release and try again")
            self.bridge.send("x")
            self.token = secrets.token_urlsafe(24)
            self.sequence = -1
            self.deadline = self.clock() + CONTROL_TIMEOUT
            return self.token

    def command(self, token, sequence, command):
        with self.lock:
            self.expire()
            if not token or token != self.token:
                raise ControlConflict("Control expired; release and press again")
            if type(sequence) is not int or sequence <= self.sequence:
                raise ControlConflict("Out-of-order command rejected")
            command = normalize_command(command)
            if not self.bridge.firmware_ready:
                self._stop()
                raise ControlConflict("UNO firmware not ready")
            self.sequence = sequence
            if command in {"x", " ", "0"}:
                self._stop()
            else:
                self.bridge.send(command)
                self.deadline = self.clock() + CONTROL_TIMEOUT

    def stop(self, token=None):
        with self.lock:
            # A late release from an old session cannot stop a new owner.
            # An explicit emergency stop (no token) is available to every client.
            if token is None or token == self.token:
                self._stop()


class RobotCarServer(ThreadingHTTPServer):
    daemon_threads = True

    def __init__(
        self,
        address: tuple[str, int],
        bridge: UnoBridge,
        events: EventLog,
    ) -> None:
        self.bridge = bridge
        self.events = events
        self.control = ControlSession(bridge)
        super().__init__(address, RobotCarHandler)

    def service_actions(self):
        try:
            self.control.expire()
        except serial.SerialException:
            pass  # Bridge marks the disconnect; UNO still has its own timeout.



class RobotCarHandler(SimpleHTTPRequestHandler):
    server: RobotCarServer

    def __init__(self, *args: object, **kwargs: object) -> None:
        super().__init__(*args, directory=str(WEB_ROOT), **kwargs)

    def setup(self):
        super().setup()
        self.connection.settimeout(2)

    def end_headers(self):
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Content-Security-Policy", "default-src 'self'; frame-ancestors 'none'")
        super().end_headers()

    def log_message(self, format: str, *args: object) -> None:
        # API requests are frequent; meaningful events are shown in EventLog.
        return

    def send_json(
        self,
        payload: dict[str, object],
        status: HTTPStatus = HTTPStatus.OK,
    ) -> None:
        encoded = json.dumps(payload).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(encoded)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(encoded)

    def do_GET(self) -> None:
        parsed = urlparse(self.path)
        if parsed.path == "/api/status":
            query = parse_qs(parsed.query)
            try:
                after = int(query.get("after", ["0"])[0])
            except ValueError:
                after = 0
            self.send_json(
                {
                    "connected": self.server.bridge.connected,
                    "firmware_ready": self.server.bridge.firmware_ready,
                    "configuration": self.server.bridge.configuration,
                    "port": self.server.bridge.port,
                    "baud": BAUD_RATE,
                    "events": self.server.events.after(after),
                }
            )
            return
        super().do_GET()

    def do_POST(self) -> None:
        if self.path not in {"/api/command", "/api/control", "/api/stop"}:
            self.send_json({"error": "Not found"}, HTTPStatus.NOT_FOUND)
            return
        # Cross-origin pages cannot submit commands using forms or simple fetch.
        # This is a trusted-LAN tool, not authentication against LAN peers.
        origin = self.headers.get("Origin")
        if (self.headers.get("X-RobotCar") != "1" or
                (origin and origin != "http://" + self.headers.get("Host", ""))):
            self.send_json({"error": "Same-origin control required"}, HTTPStatus.FORBIDDEN)
            return
        try:
            length = int(self.headers.get("Content-Length", "0"))
            if not 0 < length <= 1024:
                raise ValueError("Invalid request size")
            payload = json.loads(self.rfile.read(length))
            if not isinstance(payload, dict):
                raise ValueError("Expected a JSON object")
            if self.path == "/api/control":
                self.send_json({"token": self.server.control.acquire()})
                return
            if self.path == "/api/stop":
                self.server.control.stop(payload.get("token"))
            else:
                self.server.control.command(payload.get("token"),
                                            payload.get("sequence"),
                                            payload.get("command"))
        except ControlConflict as exc:
            self.send_json({"error": str(exc)}, HTTPStatus.CONFLICT)
            return
        except (ValueError, UnicodeError) as exc:
            self.send_json({"error": str(exc)}, HTTPStatus.BAD_REQUEST)
            return
        except serial.SerialException:
            self.send_json({"error": "UNO disconnected; restart controller"},
                           HTTPStatus.SERVICE_UNAVAILABLE)
            return
        self.send_json({"ok": True})


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run the RobotCar web controls")
    parser.add_argument("--host", default="127.0.0.1",
                        help="listen address; use 0.0.0.0 for trusted local Wi-Fi")
    parser.add_argument("--port", help="UNO serial port; detected if omitted")
    parser.add_argument(
        "--web-port",
        type=int,
        default=DEFAULT_WEB_PORT,
        help=f"local web port (default: {DEFAULT_WEB_PORT})",
    )
    parser.add_argument(
        "--no-browser",
        action="store_true",
        help="do not open the browser automatically",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    events = EventLog()
    try:
        serial_port = args.port or find_uno_port()
        bridge = UnoBridge(serial_port, events)
        bridge.start()
    except (RuntimeError, serial.SerialException) as exc:
        print(f"Cannot start controller: {exc}")
        return 1

    try:
        server = RobotCarServer((args.host, args.web_port), bridge, events)
    except OSError as exc:
        bridge.close()
        print(f"Cannot listen: {exc}")
        return 1
    url = f"http://{args.host}:{args.web_port}"
    events.add("info", f"Control page ready at {url}")

    if not args.no_browser:
        threading.Timer(0.4, webbrowser.open, args=(url,)).start()

    def terminate(signum, frame):
        raise KeyboardInterrupt

    signal.signal(signal.SIGTERM, terminate)
    try:
        server.serve_forever(poll_interval=0.05)
    except KeyboardInterrupt:
        events.add("info", "Controller interrupted")
    finally:
        server.server_close()
        bridge.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
