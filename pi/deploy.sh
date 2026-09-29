#!/usr/bin/env bash
# Run on the Mac. SSH prompts locally for the Pi password if keys are absent.
# Copies only runtime files into a new release; never starts motors or a service.
set -euo pipefail
if [[ $# -ne 1 || "$1" == -* || "$1" == *[!a-zA-Z0-9_.@:-]* ]]; then
  echo 'Usage: bash pi/deploy.sh USER@PI_HOST' >&2
  exit 2
fi
target=$1
project_dir=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd -P)
release="$(date -u +%Y%m%dT%H%M%SZ)-$$"
archive=$(mktemp -t robotcar-release)
trap 'rm -f -- "$archive"' EXIT
# Check prerequisites first; this does not open the UNO port.
ssh "$target" 'python3 -c "import serial; assert hasattr(serial, \"Serial\"), \"pyserial is required\""'
COPYFILE_DISABLE=1 tar -czf "$archive" -C "$project_dir" \
  tools/mac_web_controller.py tools/requirements-web.txt \
  tools/web/index.html tools/web/app.js tools/web/style.css pi/run.sh pi/install-service.sh
ssh "$target" "mkdir -p robotcar/releases/$release"
scp "$archive" "$target:robotcar/releases/$release/runtime.tar.gz"
ssh "$target" "set -eu
cd robotcar/releases/$release
tar -xzf runtime.tar.gz
python3 -m py_compile tools/mac_web_controller.py
cd ../..
if [ -e current ] && [ ! -L current ]; then
  echo 'robotcar/current exists and is not a symlink; leaving it unchanged.' >&2
  exit 1
fi
ln -sfn releases/$release current
"
printf '\nDeployed release %s; previous releases retained.\n' "$release"
printf 'With motor power OFF and miniterm closed, start it using:\n'
printf "ssh -t %s 'bash ~/robotcar/current/pi/run.sh'\n" "$target"
printf 'Then open http://robotcar.local:8765 on your local network.\n'
