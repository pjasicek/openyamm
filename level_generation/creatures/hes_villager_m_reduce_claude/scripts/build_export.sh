#!/usr/bin/env bash
# Reduced Landfall villager (male) runtime GLB from the picked ladder candidate (work/ladder.blend):
# export_cand.py -> swap_lod0.py (into the rollback source: materials, variants, region mask and ramps, clips, sockets
# unchanged) -> build_lods.py (LOD1; its LOD2/3 are placeholders) -> shrink_shadow_lods.py (the source project's
# margins) -> carry_variants.py -> lodrep/repair_glb.py (LOD2/LOD3 + shadows by the lod_repair_claude route: own
# UVs and far textures) -> export/hes_hvm.glb. Usage: scripts/build_export.sh Cand_73
set -euo pipefail
cd "$(dirname "$0")/.."
export CAP=${CAP:-8G}
BL="scripts/cap.sh /snap/bin/blender --background --factory-startup --threads 4 --python-exit-code 1"
VENV=/tmp/claude-1000/-home-pjasicek-github-OpenYAMM/ff001cf4-6927-455b-b1bb-249fd16968d3/scratchpad/reduce/venv/bin/python
REA_DOUBLES=work/doubles.npy REA_CAND=${1:-Cand_73} REA_NODE=HVM $BL -P scripts/export_cand.py 2>&1 | grep -E "FLOOR|EXPORTED|Error"
scripts/cap.sh python3 scripts/swap_lod0.py work/hes_hvm_source_pre_reduce.glb work/cand_export.glb work/pick_lod0.glb HVM
$BL -P scripts/build_lods.py 2>&1 | grep -E "PROTECTED|RATIOS|LOD tri|Error"
MESH=HVM scripts/cap.sh python3 scripts/shrink_shadow_lods.py work/pick_lods.glb work/pick_lods_shadowfix.glb > /dev/null
scripts/cap.sh python3 scripts/carry_variants.py work/pick_lods_shadowfix.glb
LOD_REPAIR_PYTHON=$VENV scripts/cap.sh python3 lodrep/repair_glb.py work/pick_lods_shadowfix.glb work/lodrep export/hes_hvm.glb
ls -la export/hes_hvm.glb
