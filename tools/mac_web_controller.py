#!/usr/bin/env python3
"""Serve the RobotCar keyboard UI and forward commands to an UNO over USB."""

from __future__ import annotations

import argparse
import glob
import json
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
    matches = sorted(
        {
            path
            for pattern in PORT_PATTERNS
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
        self._serial = serial.Serial(port, BAUD_RATE, timeout=0.1)
        self._write_lock = threading.Lock()
        self._stop_event = threading.Event()
        self._reader: threading.Thread | None = None
        self._last_motion: str | None = None

    def start(self) -> None:
        self.events.add("info", "Waiting two seconds for the UNO to restart")
        time.sleep(2)
        self._serial.reset_input_buffer()
        self._reader = threading.Thread(target=self._read_loop, daemon=True)
        self._reader.start()
        self.send("x")
        self.events.add("success", f"UNO connected on {self.port}")

    def send(self, command: str) -> None:
        command = command.lower()
        if len(command) != 1 or command not in ALLOWED_COMMANDS:
            raise ValueError("Unsupported command")

        try:
            with self._write_lock:
                self._serial.write(command.encode("ascii"))
                self._serial.flush()
        except serial.SerialException as exc:
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
                self.events.add("error", f"UNO connection lost: {exc}")
                return
            if line:
                message = line.decode("utf-8", errors="replace").strip()
                if message:
                    level = "warning" if "TIMEOUT" in message else "uno"
                    self.events.add(level, f"UNO: {message}")

    def close(self) -> None:
        try:
            if self._serial.is_open:
                self.send("x")
        except (serial.SerialException, ValueError):
            pass
        self._stop_event.set()
        if self._reader is not None:
            self._reader.join(timeout=0.3)
        if self._serial.is_open:
            self._serial.close()
        self.events.add("info", "Serial connection closed")


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
        super().__init__(address, RobotCarHandler)


class RobotCarHandler(SimpleHTTPRequestHandler):
    server: RobotCarServer

    def __init__(self, *args: object, **kwargs: object) -> None:
        super().__init__(*args, directory=str(WEB_ROOT), **kwargs)

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
                    "connected": self.server.bridge._serial.is_open,
                    "port": self.server.bridge.port,
                    "baud": BAUD_RATE,
                    "events": self.server.events.after(after),
                }
            )
            return
        super().do_GET()

    def do_POST(self) -> None:
        if self.path != "/api/command":
            self.send_json({"error": "Not found"}, HTTPStatus.NOT_FOUND)
            return

        try:
            length = int(self.headers.get("Content-Length", "0"))
            if length > 1024:
                raise ValueError("Request is too large")
            payload = json.loads(self.rfile.read(length))
            command = payload.get("command", "")
            if not isinstance(command, str):
                raise ValueError("Command must be text")
            self.server.bridge.send(command)
        except (ValueError, json.JSONDecodeError) as exc:
            self.send_json({"error": str(exc)}, HTTPStatus.BAD_REQUEST)
            return
        except serial.SerialException:
            self.send_json(
                {"error": "UNO serial connection failed"},
                HTTPStatus.SERVICE_UNAVAILABLE,
            )
            return

        self.send_json({"ok": True})


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run the RobotCar web controls")
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

    server = RobotCarServer(("127.0.0.1", args.web_port), bridge, events)
    url = f"http://127.0.0.1:{args.web_port}"
    events.add("info", f"Control page ready at {url}")
    events.add(
        "warning",
        "Motor power is currently unverified. Keep wheels raised for tests.",
    )

    if not args.no_browser:
        threading.Timer(0.4, webbrowser.open, args=(url,)).start()

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        events.add("info", "Controller interrupted")
    finally:
        server.shutdown()
        server.server_close()
        bridge.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
