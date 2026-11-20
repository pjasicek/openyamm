#!/usr/bin/env bash
# Grafted-heads hydra, from the fitted Smart Topology heads to the runtime GLB (README "Pipeline", steps 3-6):
# graft -> UVs -> bakes -> clips -> UV dump -> assemble -> grade -> compose -> runtime GLB -> viewer GLBs.
# Inputs: work/rig_v1.blend + work/rig.json (rig_hyd.py on red_11000), work/heads/h<k>_st.blend + h<k>_fit.json
# (head_fit.py), meshy/head<k>_retexture_v2. Pass --install to install the runtime GLB.
set -euo pipefail
here="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
b=/snap/bin/blender; s="$here/scripts"; w="$here/work"; t="$here/textures"
cd "$here"
"$b" --background "$w/rig_v1.blend" --python "$s/graft_heads.py" -- "$w/rig_graft.blend" ${HEAD_BUDGET:-} 2>&1 | grep -E "^GRAFT|^TOTAL|Error|Traceback" -A3
"$b" --background "$w/rig_graft.blend" --python "$s/uv_atlas.py" -- "$w/hd_atlas.blend" 2>&1 | grep -E "COVERAGE|Error|Traceback" -A3
"$b" --background "$w/hd_atlas.blend" --python "$s/bake_hydra.py" 2>&1 | grep -E "^SAVED|Error|Traceback" -A3
"$b" --background "$w/hd_atlas.blend" --python "$s/anim_hyd.py" 2>&1 | grep -E "^CLIP|Error|Traceback" -A3
"$b" --background "$w/anim_v1.blend" --python "$s/dump_uv3d.py" 2>&1 | grep -E "DUMPED|Error|Traceback" -A3
python3 "$s/compose_hyd.py" --assemble
python3 "$here/../claude_shared/grade_basecolor.py" --ao "$t/hyd_body_ao.png" "$t/hyd_body_basecolor.png"
python3 "$here/../claude_shared/grade_basecolor.py" --ao "$t/hyd_head_ao.png" --fine 0.85 --local 0.4 "$t/hyd_head_basecolor.png"
python3 "$s/compose_hyd.py" | cut -c1-400
bash "$s/build_runtime.sh" "${1:-}" | tail -2
python3 "$s/viewer_tiers.py"
