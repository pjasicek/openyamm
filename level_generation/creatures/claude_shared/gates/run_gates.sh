#!/usr/bin/env bash
set -euo pipefail
here="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
export OPENBLAS_NUM_THREADS=4 OMP_NUM_THREADS=4 PYTHONDONTWRITEBYTECODE=1
exec "${BLENDER:-blender}" --background --factory-startup --disable-autoexec --threads 4 \
    --python-exit-code 2 --python "$here/run_gates.py" -- "$@"
