"""Controller behavior tests with a fake UNO; no physical serial port is opened."""
import importlib.util
import json
import threading
import unittest
import time
from unittest.mock import patch, MagicMock
from http.client import HTTPConnection
from pathlib import Path

spec = importlib.util.spec_from_file_location('controller', Path(__file__).parents[1] / 'tools/mac_web_controller.py')
controller = importlib.util.module_from_spec(spec)
spec.loader.exec_module(controller)

class Bridge:
    connected = True
    port = 'fake-uno'
    firmware_ready = True
    configuration = {'protocol':2,'speed':195,'curve':75,'minimum':195,'maximum':255}
    def __init__(self): self.commands = []
    def send(self, command):
        if not self.connected: raise controller.serial.SerialException('USB removed')
        self.commands.append(command)

class ControlTests(unittest.TestCase):
    def setUp(self):
        self.now = 10.0
        self.bridge = Bridge()
        self.control = controller.ControlSession(self.bridge, lambda: self.now)

    def test_lost_browser_stops_and_old_commands_cannot_resume(self):
        token = self.control.acquire()
        self.control.command(token, 1, 'w')
        self.now += 0.31
        self.control.expire()
        self.assertEqual(self.bridge.commands[-1], 'x')
        with self.assertRaises(controller.ControlConflict):
            self.control.command(token, 2, 'w')
        self.assertEqual(self.bridge.commands[-1], 'x')

    def test_release_invalidates_in_flight_command(self):
        token = self.control.acquire()
        self.control.command(token, 1, 'w')
        self.control.stop(token)
        with self.assertRaises(controller.ControlConflict):
            self.control.command(token, 2, 'w')

    def test_second_browser_cannot_take_over(self):
        self.control.acquire()
        with self.assertRaises(controller.ControlConflict): self.control.acquire()

    def test_out_of_order_and_duplicate_commands_are_rejected(self):
        token = self.control.acquire()
        self.control.command(token, 2, 'd')
        for sequence in [1, 2, True, '3']:
            with self.assertRaises(controller.ControlConflict):
                self.control.command(token, sequence, 'w')
        self.assertEqual(self.bridge.commands[-1], 'd')

    def test_old_release_does_not_interrupt_new_owner(self):
        old = self.control.acquire()
        self.control.stop(old)
        new = self.control.acquire()
        self.control.command(new, 1, 'w')
        self.control.stop(old)
        self.assertEqual(self.bridge.commands[-1], 'w')
        self.control.stop()  # Emergency stop from any browser.
        self.assertEqual(self.bridge.commands[-1], 'x')

    def test_heartbeat_extends_lease_but_server_does_not_repeat(self):
        token = self.control.acquire()
        for sequence in range(5):
            self.now += .1
            self.control.command(token, sequence, 'w')
            self.control.expire()
        self.assertEqual(self.bridge.commands.count('w'), 5)

    def test_expired_speed_command_cannot_restart_motion(self):
        token = self.control.acquire()
        self.control.command(token, 1, 'w')
        self.now += .31
        with self.assertRaises(controller.ControlConflict):
            self.control.command(token, 2, '+')
        self.assertEqual(self.bridge.commands[-1], 'x')

    def test_failed_stop_still_invalidates_lease(self):
        token = self.control.acquire()
        self.bridge.connected = False
        with self.assertRaises(controller.serial.SerialException): self.control.stop(token)
        self.assertIsNone(self.control.token)
        with self.assertRaises(controller.serial.SerialException): self.control.acquire()

    def test_curve_setting_validation_and_ordering(self):
        token = self.control.acquire()
        self.control.command(token, 1, '@c75')
        self.assertEqual(self.bridge.commands[-1], '@c75')
        for value in ['@c101', '@c-1', '@c75\nw', '@c1.5', '@c', '@c00']:
            with self.assertRaises(ValueError): self.control.command(token, 2, value)
        self.control.stop(token)
        with self.assertRaises(controller.ControlConflict):
            self.control.command(token, 3, '@c100')

    def test_old_firmware_cannot_acquire_control(self):
        self.bridge.firmware_ready = False
        with self.assertRaises(controller.ControlConflict): self.control.acquire()
        self.assertEqual(self.bridge.commands, [])

class BridgeTests(unittest.TestCase):
    def test_shutdown_stops_and_rejects_further_writes(self):
        fake = MagicMock()
        fake.is_open = True
        with patch.object(controller.serial, 'Serial', return_value=fake):
            bridge = controller.UnoBridge('fake', controller.EventLog())
        bridge.send('w')
        bridge.close()
        with self.assertRaises(controller.serial.SerialException): bridge.send('w')
        self.assertEqual([call.args[0] for call in fake.write.call_args_list], [b'w', b'x'])
        self.assertFalse(bridge.connected)

    def test_reader_failure_marks_connection_unhealthy(self):
        fake = MagicMock()
        fake.is_open = True
        fake.readline.side_effect = controller.serial.SerialException('USB removed')
        with patch.object(controller.serial, 'Serial', return_value=fake):
            bridge = controller.UnoBridge('fake', controller.EventLog())
        bridge._read_loop()
        self.assertFalse(bridge.connected)

    def test_firmware_settings_and_serial_framing(self):
        fake = MagicMock()
        fake.is_open = True
        with patch.object(controller.serial, 'Serial', return_value=fake):
            bridge = controller.UnoBridge('fake', controller.EventLog())
        self.assertFalse(bridge.firmware_ready)
        bridge.read_configuration('CONFIG: protocol=2 speed=195 curve=75 min=195 max=255')
        self.assertTrue(bridge.firmware_ready)
        self.assertEqual(bridge.configuration['curve'], 75)
        bridge.send('@c100')
        fake.write.assert_called_with(b'@c100\n')
        bridge.read_configuration('ROBOTCAR READY')
        self.assertFalse(bridge.firmware_ready)

    def test_stable_linux_path_preferred(self):
        def paths(pattern):
            return ['/dev/serial/by-id/uno'] if pattern == '/dev/serial/by-id/*' else ['/dev/ttyACM0']
        with patch.object(controller.glob, 'glob', side_effect=paths):
            self.assertEqual(controller.find_uno_port(), '/dev/serial/by-id/uno')

    def test_multiple_devices_require_selection(self):
        with patch.object(controller.glob, 'glob', return_value=['uno', 'nicla']):
            with self.assertRaises(RuntimeError): controller.find_uno_port()

class HTTPTests(unittest.TestCase):
    def setUp(self):
        self.bridge = Bridge()
        self.server = controller.RobotCarServer(('127.0.0.1', 0), self.bridge, controller.EventLog())
        self.thread = threading.Thread(target=self.server.serve_forever, kwargs={'poll_interval': .01})
        self.thread.start()
        self.port = self.server.server_port
    def tearDown(self):
        self.server.shutdown()
        self.server.server_close()
        self.thread.join()
    def request(self, path, payload=None, headers=None, method='POST'):
        conn = HTTPConnection('127.0.0.1', self.port, timeout=2)
        conn.request(method, path, json.dumps(payload) if payload is not None else None,
                     headers if headers is not None else {'X-RobotCar':'1','Content-Type':'application/json'})
        response = conn.getresponse()
        result = response.read().decode()
        status = response.status
        conn.close()
        return status, result
    def test_browser_to_serial_and_status(self):
        status, body = self.request('/api/control', {})
        self.assertEqual(status, 200)
        token = json.loads(body)['token']
        status, _ = self.request('/api/command', {'token':token,'sequence':1,'command':'w'})
        self.assertEqual(status, 200)
        self.assertEqual(self.bridge.commands[-1], 'w')
        self.request('/api/stop', {'token':token})
        self.assertEqual(self.bridge.commands[-1], 'x')
        self.bridge.connected = False
        _, body = self.request('/api/status', method='GET')
        self.assertFalse(json.loads(body)['connected'])
    def test_server_timer_expires_silent_browser(self):
        _, body = self.request('/api/control', {})
        token = json.loads(body)['token']
        self.request('/api/command', {'token':token,'sequence':1,'command':'w'})
        time.sleep(.4)
        self.assertEqual(self.bridge.commands[-1], 'x')
        status, _ = self.request('/api/command', {'token':token,'sequence':2,'command':'w'})
        self.assertEqual(status, 409)

    def test_web_assets_are_served(self):
        for path, content in [('/', 'Drive console'), ('/app.js', '/api/control'), ('/style.css', '.key')]:
            status, body = self.request(path, method='GET')
            self.assertEqual(status, 200)
            self.assertIn(content, body)
    def test_cross_origin_and_simple_requests_rejected(self):
        for headers in [{}, {'X-RobotCar':'1','Origin':'http://unrelated.example'}, {'X-RobotCar':'1','Origin':'null'}]:
            status, _ = self.request('/api/control', {}, headers=headers)
            self.assertEqual(status, 403)
        self.assertEqual(self.bridge.commands, [])
    def test_malformed_json_shape_rejected(self):
        for payload in [[], 'w', 1]:
            status, _ = self.request('/api/command', payload)
            self.assertEqual(status, 400)

if __name__ == '__main__': unittest.main()
