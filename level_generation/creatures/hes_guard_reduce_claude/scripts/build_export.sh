#!/usr/bin/env bash
# Reduced Landfall Guard runtime GLB from the picked ladder candidate (work/ladder.blend):
# export_cand.py -> swap_lod0.py (into the rollback source: materials, variants, region mask and ramps, clips, sockets
# unchanged) -> build_lods.py (LOD1; its LOD2/3 are placeholders) -> shrink_shadow_lods.py (the source project's
# margins) -> carry_variants.py -> lodrep/repair_glb.py (LOD2/LOD3 + shadows by the lod_repair_claude route: own
# UVs and far textures) -> work/floor_fix_base/hes_guard.glb (pre-floor-fix export) -> ground_body.py, floor_fix.py
# --lift-joints/--ground-death, death_rifle_floor.py (corpse on the floor, rifle laid down) -> export/hes_guard.glb. Usage: scripts/build_export.sh Cand_84
set -euo pipefail
cd "$(dirname "$0")/.."
export CAP=${CAP:-8G}
BL="scripts/cap.sh /snap/bin/blender --background --factory-startup --threads 4 --python-exit-code 1"
VENV=/tmp/claude-1000/-home-pjasicek-github-OpenYAMM/ff001cf4-6927-455b-b1bb-249fd16968d3/scratchpad/reduce/venv/bin/python
REA_CAND=${1:-Cand_84} REA_NODE=HGD $BL -P scripts/export_cand.py 2>&1 | grep -E "FLOOR|EXPORTED|Error"
scripts/cap.sh python3 scripts/swap_lod0.py work/hes_guard_source_pre_reduce.glb work/cand_export.glb work/pick_lod0.glb HGD
$BL -P scripts/build_lods.py 2>&1 | grep -E "PROTECTED|RATIOS|LOD tri|Error"
MESH=HGD scripts/cap.sh python3 scripts/shrink_shadow_lods.py work/pick_lods.glb work/pick_lods_shadowfix.glb > /dev/null
scripts/cap.sh python3 scripts/carry_variants.py work/pick_lods_shadowfix.glb
LOD_REPAIR_PYTHON=$VENV scripts/cap.sh python3 lodrep/repair_glb.py work/pick_lods_shadowfix.glb work/lodrep work/floor_fix_base/hes_guard.glb
# corpse floor fix (2026-10-22): body onto the floor without the hanging skirt, skirt strips lifted, rifle laid down
python3 scripts/ground_body.py work/floor_fix_base/hes_guard.glb work/floor_s1.glb
python3 ../claude_shared/floor/floor_fix.py work/floor_s1.glb work/floor_s2.glb --lift-joints Death Dead --lift-only 'Robe_*' --ground-death Death Dead
python3 scripts/death_rifle_floor.py work/floor_s2.glb export/hes_guard.glb export/hes_guard_rifle.glb
python3 scripts/check_key_times.py export/hes_guard.glb export/hes_guard_rifle.glb export/hes_guard_rifle_glow.glb
ls -la export/hes_guard.glb
