#!/usr/bin/env bash
# Sven's linings (LINING_BRIEF_20261105.md): installed GLB (before/) -> export/mm9_sven.glb, faces added only.
# The hair selection reads the see-through gate's hole_faces of the installed GLB (review/gates_hitlog/, made by
#   scripts/bl.sh <log> level_generation/creatures/mm9_sven_lining_claude/scripts/see_through_gate.py \
#     before/mm9_sven.glb review/gates_hitlog/see_through.json step=4 px_mm=4 shots=1 extra=   (absolute paths)).
# Usage (project folder): scripts/build.sh [extra glb_lining.py key=value ...]
set -euo pipefail
cd "$(dirname "$0")/.."
mkdir -p export review
systemd-run --user --scope -q -p MemoryMax=12G -p MemorySwapMax=0 python3 scripts/glb_lining.py before/mm9_sven.glb \
  export/mm9_sven.glb review/lining_report.json hair_hits=review/gates_hitlog/see_through.json "$@" | cut -c1-400
sha256sum export/mm9_sven.glb
