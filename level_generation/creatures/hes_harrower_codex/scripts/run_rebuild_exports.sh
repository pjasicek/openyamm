#!/usr/bin/env bash
# Rebuild every runtime export from work/final.blend: README steps 1-4 with the unchanged LOD plan.
# export_harrower.py, prepare_materials.py, build_lods.py, split_models.py; prepare_repair.py prepare / lod_audit.py /
# prepare_repair.py finish per review/lod_plan.json asset; assemble_lod_audit.py, lod_audit.py per tier, check_lods.py;
# runtime_finish.py, make_binding.py, validate_exports.py, viewer_tiers.py, prepare_viewer.py. Env as run_lib.sh.
set -euo pipefail
source "$(dirname "$0")/run_lib.sh"
blend export export_harrower.py "$W/work/final.blend"
grep ASSEMBLY "$LOG/export.log" | cut -c1-300
py prepare_materials "$W"/scripts/prepare_materials.py
blend build_lods build_lods.py
py split_models "$W"/scripts/split_models.py
for item in $(python3 -c "import json;print(' '.join(f'{k}:{v}' for k,v in json.load(open('review/lod_plan.json'))['asset_steps'].items()))"); do
    stem=${item%%:*}; step=${item#*:}
    py "repair_prepare_$stem" "$W"/scripts/prepare_repair.py prepare "$stem" "$step"
    blend "lod_audit_$stem" lod_audit.py "$stem" "$step"
    py "repair_finish_$stem" "$W"/scripts/prepare_repair.py finish "$stem" "$step"
    tail -1 "$LOG/repair_finish_$stem.log" | cut -c1-200
done
py assemble_lod_audit "$W"/scripts/assemble_lod_audit.py
for tier in a b c boss; do blend "lod_audit_assembly_$tier" lod_audit.py "assembly_$tier" repaired; done
py check_lods "$W"/scripts/check_lods.py
cut -c1-200 "$LOG/check_lods.log"
py runtime_finish "$W"/scripts/runtime_finish.py
py make_binding "$W"/scripts/make_binding.py
py validate_exports "$W"/scripts/validate_exports.py
tail -2 "$LOG/validate_exports.log" | cut -c1-400
py viewer_tiers "$W"/scripts/viewer_tiers.py
py prepare_viewer "$W"/scripts/prepare_viewer.py
echo "== exports done"
