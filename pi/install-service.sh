#!/usr/bin/env bash
# Run on the Pi using sudo; the controller itself runs as the normal Pi user.
set -euo pipefail
if [[ $EUID -ne 0 ]]; then
  echo 'Run: sudo bash ~/robotcar/current/pi/install-service.sh' >&2
  exit 1
fi
service_user=${1:-${SUDO_USER:-}}
if [[ ! "$service_user" =~ ^[a-z_][a-z0-9_-]*$ || "$service_user" == root ]]; then
  echo 'Specify the normal Pi account, not root.' >&2
  exit 1
fi
service_home=$(getent passwd "$service_user" | cut -d: -f6)
if [[ ! "$service_home" =~ ^/[a-zA-Z0-9_/-]+$ ]]; then
  echo 'Unsupported or missing home directory.' >&2
  exit 1
fi
runtime="$service_home/robotcar/current/pi/run.sh"
test -r "$runtime"
/usr/bin/python3 -c 'import serial; assert hasattr(serial, "Serial")'
getent group dialout >/dev/null
unit=$(mktemp)
trap 'rm -f -- "$unit"' EXIT
cat > "$unit" <<UNIT
[Unit]
Description=RobotCar browser controller
After=network.target
StartLimitIntervalSec=0

[Service]
Type=exec
User=$service_user
SupplementaryGroups=dialout
WorkingDirectory=$service_home/robotcar/current
Environment=ROBOTCAR_PYTHON=/usr/bin/python3
ExecStart=/bin/bash $runtime
Restart=on-failure
RestartSec=5
TimeoutStopSec=5
KillSignal=SIGTERM
NoNewPrivileges=true
PrivateTmp=true
UMask=0077

[Install]
WantedBy=multi-user.target
UNIT
# Stop an existing managed instance; reject a competing manual controller.
if systemctl cat robotcar.service >/dev/null 2>&1; then
  systemctl stop robotcar.service
fi
/usr/bin/python3 - <<'CHECK'
import socket
with socket.socket() as listener:
    listener.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    try:
        listener.bind(('0.0.0.0', 8765))
    except OSError:
        raise SystemExit('Port 8765 is busy. Stop the manual controller with Ctrl+C, then rerun this installer.')
CHECK
install -m 644 "$unit" /etc/systemd/system/robotcar.service
systemctl daemon-reload
systemctl enable robotcar.service
systemctl restart robotcar.service
# Starting a process does not imply that serial initialization succeeded.
/usr/bin/python3 - <<'PY'
import json, time, urllib.request
for _ in range(20):
    try:
        with urllib.request.urlopen('http://127.0.0.1:8765/api/status', timeout=1) as response:
            status = json.load(response)
        if status.get('connected') and status.get('firmware_ready'):
            print('Controller ready. Open http://robotcar.local:8765')
            break
    except (OSError, ValueError):
        pass
    time.sleep(1)
else:
    raise SystemExit('Service enabled, but UNO is not ready. Check: sudo journalctl -u robotcar -n 40 --no-pager')
PY
systemctl --no-pager --full status robotcar.service
