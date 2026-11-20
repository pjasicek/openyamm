#!/bin/bash
# Runtime build + viewer GLBs + manifest (project folder). Usage: TOKEN=<lease> scripts/rebuild.sh <viewer revision> [--install]
# Texture chain before it (only when the paint changes): scripts/tex_fix.py -> grade_basecolor.py (gentle) ->
# scripts/neck_match.py -> scripts/tier_ramps.py. Master: v2/work/fix_v2.blend (scripts/geo_fix.py on v2/work/head_uv.blend -> fix_v1,
# then scripts/neck_hole.py fix_v1 -> fix_v2: the see-through hole under the right jaw, ear sweep 2026-11-02).
set -euo pipefail
cd "$(dirname "$0")/.."
V=$PWD/../claude_shared/gltf_venv/bin/python
PATH=$(dirname $V):$PATH PYGLTF_PYTHON=$V BLEND=v2/work/fix_v2.blend BODYTEX=pm1d HEADTEX=pm1d \
  v2/scripts/build_runtime_v2.sh pm1d PM1d v2/scripts/roles_pm1d.json ${2:-} 2>&1 | grep -v RuntimeWarning | grep -E "HANDREST|LOD tri|WINDING|Error|FAIL|install|Installed|wrote" | cut -c1-200
$V v2/scripts/viewer_tiers.py pm1d PM1d 2>&1 | grep -c viewer
python3 v2/scripts/make_viewer_tiers.py "$1" "pm1d_c=Row 22 Commoner (PeasantM1c)=review/viewer/pm1d_c.glb" \
  "pm1d_d=Row 28 Prisoner (PeasantM1d)=review/viewer/pm1d_d.glb" > /dev/null
