#!/usr/bin/env bash
# Before/after sheet of the see-through openings (2026-11-02): closeup.py on the review viewer GLBs (tiers baked), back
# faces culled as in the game. Before = work/rollback_r6/pdm2_{a,b}.glb, after = review/viewer/pdm2_{a,b}.glb.
# Rows: Running frame 12 front (the user's shot) whole legs-to-chest, frame 16 (the pose of the user's screenshot: the
# viewer's frame counter is not our 30 fps index) with its cuff and boot tops, then both cuffs and boot tops at 12,
# then the worst frames of the see-through gate (r6) at their own view. Usage (project folder): scripts/holes_sheet.sh
set -euo pipefail
OUT=review/holes_sheet; mkdir -p $OUT
SPECS=(
  "run12|Running|12|Bip01 Spine|0|0|0.95"
  "run16|Running|16|Bip01 Spine|0|0|0.95"
  "run16_cuffL|Running|16|Bip01 L Hand|0|0|0.25"
  "run16_bootL|Running|16|Bip01 L Calf@0.2|0|0|0.3"
  "run16_bootR|Running|16|Bip01 R Calf@0.2|0|0|0.3"
  "run12_cuffL|Running|12|Bip01 L Hand|0|0|0.25"
  "run12_cuffR|Running|12|Bip01 R Hand|0|0|0.25"
  "run12_bootL|Running|12|Bip01 L Calf@0.2|0|0|0.3"
  "run12_bootR|Running|12|Bip01 R Calf@0.2|0|0|0.3"
  "run15_bootL|Running|15|Bip01 L Calf@0.2|0|20|0.3"
  "w_cuffR_attack28|AttackMelee|28|Bip01 R Hand|45|20|0.3"
  "w_cuffL_rubbeard66|RubBeard|66|Bip01 L Hand|0|0|0.3"
  "w_cuffL_death16|Death|16|Bip01 L Hand|315|0|0.3"
  "w_bootL_run18|Running|18|Bip01 L Calf@0.2|315|0|0.3"
  "w_bootR_run6|Running|6|Bip01 R Calf@0.2|0|0|0.3"
  "w_bootL_dump16|Dump|16|Bip01 L Calf@0.2|0|0|0.3"
  "w_torso_death30|Death|30|Bip01 Spine1|90|0|0.5"
)
for t in a b; do
  /snap/bin/blender --background --factory-startup --disable-autoexec --python scripts/closeup.py -- \
    "$PWD/work/rollback_r6/pdm2_$t.glb" "$PWD/$OUT/before_$t" a "${SPECS[@]}" 2>&1 | grep -c CLOSEUP
  /snap/bin/blender --background --factory-startup --disable-autoexec --python scripts/closeup.py -- \
    "$PWD/review/viewer/pdm2_$t.glb" "$PWD/$OUT/after_$t" a "${SPECS[@]}" 2>&1 | grep -c CLOSEUP
done
rows=()
for s in "${SPECS[@]}"; do
  n=${s%%|*}; rest=${s#*|}; clip=${rest%%|*}; rest=${rest#*|}; f=${rest%%|*}
  rows+=("$n|$clip $f=$OUT/before_a/$n.png,$OUT/after_a/$n.png,$OUT/before_b/$n.png,$OUT/after_b/$n.png")
done
python3 scripts/grid_sheet.py review/sheet_holes_before_after.png 300 \
  "PeasantDM2 see-through openings: r6 (before) vs r7 (linings), back faces culled; grey = background" \
  "tier A r6,tier A r7,tier B r6,tier B r7" "${rows[@]}"
