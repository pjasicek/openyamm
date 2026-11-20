#!/usr/bin/env bash
# Reduced Devil runtime GLB from the picked ladder candidate: export_cand.py -> swap_lod0.py (into the rollback
# source: materials, variants, region ramps and clips unchanged) -> build_lods.py -> shrink_shadow_lods.py ->
# carry_variants.py. Smooth shading -> export/mm7_m178.glb; REA_FLAT=1 -> export/mm7_m178_flat.glb (flat shading as
# the Batch E export). Usage: [REA_FLAT=1] scripts/build_export.sh [Cand_75]
set -euo pipefail
cd "$(dirname "$0")/.."
export CAP=${CAP:-8G}
BL="scripts/cap.sh /snap/bin/blender --background --factory-startup --threads 4 --python-exit-code 1"
out=export/mm7_m178.glb; [ "${REA_FLAT:-0}" = 1 ] && out=export/mm7_m178_flat.glb
REA_CAND=${1:-Cand_75} REA_NODE=Devil $BL -P scripts/export_cand.py 2>&1 | grep -E "FLOOR|EXPORTED|Error"
scripts/cap.sh python3 scripts/swap_lod0.py work/mm7_m178_source_pre_reduce.glb work/cand_export.glb work/pick_lod0.glb Devil
$BL -P scripts/build_lods.py 2>&1 | grep -E "PROTECTED|LOD tri|Error"
scripts/cap.sh python3 scripts/shrink_shadow_lods.py work/pick_lods.glb work/pick_lods_shadowfix.glb > /dev/null
cp work/pick_lods_shadowfix.glb $out
scripts/cap.sh python3 scripts/carry_variants.py $out
ls -la $out
