#!/bin/bash
# Rebuild from the paid paints (project folder): scripts/rebuild.sh <viewer revision> [--install]
# finish (grade) -> tiers (mask, ramps) -> finish (table) -> line_rims (caps, collar lining) -> rig (weights, clips) -> runtime -> viewer.
set -euo pipefail
cd "$(dirname "$0")/.."
G=../claude_shared/gltf_venv/bin/python
export HEADN=textures/pf_head_normal.png      # Meshy's head normal unchanged (coordinator 2026-11-02: never flatten it over the nose and mouth)
python3 scripts/finish_pf.py > /dev/null && $G -W ignore scripts/tiers_pf6.py 2>&1 | grep -E "Error|TIERS" && python3 scripts/finish_pf.py | tail -1 | cut -c1-80
python3 scripts/line_rims.py work/uv_tex.npz work/uv_lined.npz textures/pf_body_tone.png textures/pf_body_mask.png 0.10 0.003 | cut -c1-120
scripts/rig.sh work/uv_lined.npz 2>&1 | grep -E "Error|Trace|HALF"
scripts/build_runtime.sh ${2:-} 2>&1 | grep -E "Error|Trace|WINDING|LOD tri|Installed|installed|mm9_peasantf6.glb"
scripts/viewer_update.sh $1 | tail -1
