#!/bin/bash
# Runtime build for mm9_markel (project folder): scripts/build.sh [--install]
cd "$(dirname "$0")/.."
PYGLTF_PYTHON="$(cd ../claude_shared/gltf_venv/bin && pwd)/python" PYTHONPATH=/usr/lib/python3/dist-packages \
  TOKEN=$(cut -d' ' -f3 LEASE_TOKEN.txt) BLEND=${BLEND:-work/texpass_head.blend} BODYTEX=mk_tp HEADTEX=mk_tp \
  scripts/build_runtime_v2.sh mk Markel scripts/roles_mk.json "$@" 2>&1 | grep -v "RuntimeWarning\|frozen site"
