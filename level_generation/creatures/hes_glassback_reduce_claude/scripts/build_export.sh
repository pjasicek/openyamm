#!/usr/bin/env bash
# Reduced Glassback runtime GLB from the picked ladder candidate (work/ladder_<label>.blend, Cand_NN):
# export_cand.py -> swap_lod0.py (into the rollback source: merged body+head material, variants hgb_a/b/c, region
# mask and ramps, clips, Socket_Beak unchanged) -> build_lods.py (LOD1 at 50 %, extremes + Death/Dead floor contacts
# locked) -> shrink_shadow_lods.py (the source project's) -> carry_variants.py -> lodrep/repair_glb.py (LOD2/LOD3 +
# shadows by the lod_repair_claude route, RGBA region mask) -> work/floor_fix_base/hes_glassback.glb -> floor_fix.py
# --ground-death Death Dead (as the source build: corpse exactly on the floor) -> export/hes_glassback.glb; the 14 crest
# attachments are copied unchanged (see README). Usage: scripts/build_export.sh e Cand_80
set -euo pipefail
cd "$(dirname "$0")/.."
export CAP=${CAP:-8G}
BL="scripts/cap.sh /snap/bin/blender --background --factory-startup --threads 4 --python-exit-code 1"
VENV=/tmp/claude-1000/-home-pjasicek-github-OpenYAMM/ff001cf4-6927-455b-b1bb-249fd16968d3/scratchpad/reduce/venv/bin/python
cp work/ladder_$1.blend work/ladder.blend
REA_CAND=$2 REA_NODE=Glassback $BL -P scripts/export_cand.py 2>&1 | grep -E "FLOOR|EXPORTED|Error"
scripts/cap.sh python3 scripts/swap_lod0.py work/hes_glassback_source_pre_reduce.glb work/cand_export.glb work/pick_lod0.glb Glassback
REA_NODE=Glassback $BL -P scripts/build_lods.py 2>&1 | grep -E "PROTECTED|RATIOS|LOD tri|Error"
scripts/cap.sh python3 scripts/shrink_shadow_lods.py work/pick_lods.glb work/pick_lods_shadowfix.glb > /dev/null
scripts/cap.sh python3 scripts/carry_variants.py work/pick_lods_shadowfix.glb
mkdir -p work/floor_fix_base
LOD_REPAIR_PYTHON=$VENV scripts/cap.sh python3 lodrep/repair_glb.py work/pick_lods_shadowfix.glb work/lodrep work/floor_fix_base/hes_glassback.glb
python3 ../claude_shared/floor/floor_fix.py work/floor_fix_base/hes_glassback.glb export/hes_glassback.glb --ground-death Death Dead
for f in work/hes_glassback_crest_*_source_pre_reduce.glb; do b=$(basename $f _source_pre_reduce.glb); cp $f export/$b.glb; done
cp ../hes_glassback_claude/export/crest_info.json export/crest_info.json
python3 scripts/check_key_times.py export/*.glb | grep -v "0 samplers"
python3 scripts/floor_gate.py export/hes_glassback.glb | grep "GATE\|STRIDE\|STAND"
ls -la export/hes_glassback.glb
