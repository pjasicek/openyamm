#!/usr/bin/env bash
# Reduced drone runtime GLB from the picked ladder candidate (work/ladder_<label>.blend, Cand_NN):
# export_cand.py -> swap_lod0.py (into the rollback source: materials, variants, region masks and ramps, thrust node,
# clips, sockets unchanged) -> build_lods.py (LOD1 at 50 %, extremes + Death/Dead floor contacts locked) ->
# shrink_shadow_lods.py (the source project's turret margins) -> carry_variants.py -> lodrep/repair_glb.py (LOD2/LOD3
# + shadows by the lod_repair_claude route: own UVs and far textures, RGBA region mask) -> export/hes_drone.glb;
# the four gear attachments are copied unchanged. Usage: scripts/build_export.sh f Cand_87
set -euo pipefail
cd "$(dirname "$0")/.."
export CAP=${CAP:-8G}
BL="scripts/cap.sh /snap/bin/blender --background --factory-startup --threads 4 --python-exit-code 1"
VENV=/tmp/claude-1000/-home-pjasicek-github-OpenYAMM/ff001cf4-6927-455b-b1bb-249fd16968d3/scratchpad/reduce/venv/bin/python
cp work/ladder_$1.blend work/ladder.blend
REA_CAND=$2 REA_NODE=HDR $BL -P scripts/export_cand.py 2>&1 | grep -E "FLOOR|EXPORTED|Error"
scripts/cap.sh python3 scripts/swap_lod0.py work/hes_drone_source_pre_reduce.glb work/cand_export.glb work/pick_lod0.glb HDR
REA_NODE=HDR $BL -P scripts/build_lods.py 2>&1 | grep -E "PROTECTED|RATIOS|LOD tri|Error"
MESH=HDR scripts/cap.sh python3 scripts/shrink_shadow_lods.py work/pick_lods.glb work/pick_lods_shadowfix.glb > /dev/null
scripts/cap.sh python3 scripts/carry_variants.py work/pick_lods_shadowfix.glb
LOD_REPAIR_PYTHON=$VENV scripts/cap.sh python3 lodrep/repair_glb.py work/pick_lods_shadowfix.glb work/lodrep export/hes_drone.glb
for g in twin_emitter twin_emitter_glow shield_ring shield_ring_glow; do
  cp work/hes_drone_${g}_source_pre_reduce.glb export/hes_drone_$g.glb
done
python3 scripts/check_key_times.py export/hes_drone*.glb
python3 scripts/floor_check.py export/hes_drone.glb
ls -la export/
