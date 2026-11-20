#!/bin/bash
# Rebuild from the paid paints after a texture or weight change (project folder): scripts/rebuild.sh <viewer revision> [--install]
set -euo pipefail
cd "$(dirname "$0")/.."
G=../claude_shared/gltf_venv/bin/python
export HEADN=$( [ -f textures/pf_head_normal_face.png ] && echo textures/pf_head_normal_face.png || echo textures/pf_head_normal_fix.png ); python3 scripts/finish_pf.py > /dev/null && $G -W ignore scripts/tiers_pf5.py 2>&1 | grep -E "Error|TIERS" && python3 scripts/finish_pf.py | tail -1 | cut -c1-60
python3 scripts/tweak_pf.py work/asm_frozen.npz work/uv_tex.npz work/uv_tex2.npz 0.010 0 | tail -1
scripts/rig.sh work/uv_tex2.npz 2>&1 | grep -E "Error|Trace|HALF"
scripts/build_runtime.sh ${2:-} 2>&1 | grep -E "Error|Trace|WINDING|Installed|installed|mm9_peasantf5.glb"
scripts/viewer_update.sh $1 | tail -1
