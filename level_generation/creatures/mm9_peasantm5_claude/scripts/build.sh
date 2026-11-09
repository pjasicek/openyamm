#!/bin/bash
# Runtime build for mm9_peasantm5 (project folder): scripts/build.sh [--install]   (BLEND, BODYTEX, HEADTEX overridable)
cd "$(dirname "$0")/.."
PYGLTF_PYTHON="$(cd ../claude_shared/gltf_venv/bin && pwd)/python" PYTHONPATH=/usr/lib/python3/dist-packages \
  TOKEN=$(cat LEASE_TOKEN.txt) BLEND=${BLEND:-work/strip_m5_v1.blend} BODYTEX=${BODYTEX:-pm5_tp} HEADTEX=${HEADTEX:-pm5_tp} \
  systemd-run --user --scope -q -p MemoryMax=12G -p MemorySwapMax=0 \
  scripts/build_runtime_v2.sh pm5 PeasantM5 scripts/roles_pm5.json "$@" 2>&1 | grep -v "RuntimeWarning\|frozen site"
