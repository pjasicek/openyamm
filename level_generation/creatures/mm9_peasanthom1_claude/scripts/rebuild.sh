#!/bin/bash
# Runtime build + viewer GLBs + manifest (project folder). Usage: TOKEN=<lease> scripts/rebuild.sh <viewer revision> [--install]
# Texture chain (only when the paint changes): grade -> collar_fix.py -> sleeve_paint_fix.py; compose_headhand -> hairline_fix.py ->
# hand_clean.py (from v2/) -> fix_sideburn_phom1.py colour; tier_ramps_phom1.py -> fix_sideburn_phom1.py mask.
# Master: BLEND (default v2/work/fix_v2.blend = scripts/cuff_fix.py on v2/work/head_uv.blend, then scripts/sleeve_tuck.py 0.75 0.003 -> fix_v2, scripts/sleeve_holes.py -> fix_v3).
set -euo pipefail
cd "$(dirname "$0")/.."
V=$PWD/../claude_shared/gltf_venv/bin/python
PATH=$(dirname $V):$PATH PYGLTF_PYTHON=$V BLEND=${BLEND:-v2/work/fix_v3.blend} BODYTEX=phom1 HEADTEX=phom1 \
  v2/scripts/build_runtime_v2.sh phom1 PHOM1 v2/scripts/roles_phom1.json ${2:-} 2>&1 | grep -v RuntimeWarning | grep -E "HANDREST|LOD tri|WINDING|inverted|Error|FAIL|install|Installed|wrote|CLIPS" | cut -c1-300
$V v2/scripts/viewer_tiers.py phom1 PHOM1 2>&1 | grep -c viewer
python3 v2/scripts/make_viewer_tiers.py "$1" "phom1_a=Rows 57 Commoner, 60 Prisoner (PeasantHOM1a)=review/viewer/phom1_a.glb" \
  "phom1_b=Row 58 Town (PeasantHOM1b)=review/viewer/phom1_b.glb" > /dev/null
