#!/usr/bin/env bash
# Rebuild the picked candidate (set a, ladder e step r48) from the installed GLB in before/. Run from anywhere.
set -euo pipefail
cd "$(dirname "$0")/.."
G="../claude_shared/gltf_venv/bin/python -W ignore"
BL="scripts/cap.sh /snap/bin/blender --background --factory-startup --threads 4 --python-exit-code 1"
REA_GLB=level_generation/creatures/mm9_mummy_reduce_claude/before/mm9_mummy.glb REA_NODE=Mummy $BL -P scripts/import_source.py
REA_PROTECT=Head $BL -P scripts/dump_mesh.py
$G scripts/tex_extract.py
$G scripts/make_sets.py a              # classes: body, hands, strips (exact), face + eyes (exact), hood; soles and neck seam exact
# hands 0.6, head set kept whole (hood 1.0), body 0.48; seam slides on body and hands, texture weight 4, stretch and chart guards
SETS=a MP_SEAM_GROUPS=0,1 MP_W5=4 MP_ANISO=1.6 MP_CHART=1 MP_GROUPS=1:0.6,2:1.0 scripts/run_mp.sh e 0.48
LOD_BODY=0.55,0.22,0.10 scripts/build_mp.sh mp_e_r48 export/mm9_mummy.glb
