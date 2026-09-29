#!/usr/bin/env bash
set -euo pipefail
project_dir=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd -P)
python_bin=${ROBOTCAR_PYTHON:-python3}
exec "$python_bin" -u "$project_dir/tools/mac_web_controller.py" --host 0.0.0.0 --no-browser "$@"
