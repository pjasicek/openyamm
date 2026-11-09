#!/usr/bin/env bash
# Runtime build with this project's settings (project folder). Args passed on (e.g. --install).
cd "$(dirname "$0")/.."
PYGLTF_PYTHON=$PWD/../claude_shared/gltf_venv/bin/python TOKEN=$(cat LEASE_TOKEN.txt) HEADTEX=try_tp BODYTEX=try_tp \
  BLEND=${BLEND:-work/eyes_v3.blend} PYTHONPATH=/usr/lib/python3/dist-packages \
  bash scripts/build_runtime_v2.sh try Tryggva scripts/roles_try.json "$@" 2>&1 | grep -v RuntimeWarning
