#!/usr/bin/env bash
# Picked candidate -> export/mm8_m436.glb: export_cand (Cand_72 of work/ladder.blend = ladder_i) -> swap_lod0 ->
# build_lods -> shrink_shadow_lods (the m436 project's shadow tuck) -> carry_variants -> shared gates.
set -euo pipefail; cd "$(dirname "$0")/.."; R=../../..
REA_CAND=Cand_72 REA_NODE=M436 blender -b -P scripts/export_cand.py 2>&1 | grep EXPORTED
python3 scripts/swap_lod0.py work/mm8_m436_source_pre_reduce.glb work/cand_export.glb work/r72_lod0.glb M436
blender -b -P scripts/build_lods.py 2>&1 | grep -E "PROTECTED|LOD triangles"
python3 scripts/shrink_shadow_lods.py export/mm8_m436_lods.glb export/mm8_m436_lods_shadowfix.glb
cp export/mm8_m436_lods_shadowfix.glb export/mm8_m436.glb; python3 scripts/carry_variants.py export/mm8_m436.glb
(cd $R && level_generation/creatures/claude_shared/gates/run_gates.sh level_generation/creatures/mm8_m436_reduce_claude/export/mm8_m436.glb \
  --config level_generation/creatures/mm8_m436_claude/gates.json --out level_generation/creatures/mm8_m436_reduce_claude/review/gates \
  > level_generation/creatures/mm8_m436_reduce_claude/work/gates.log 2>&1) || true
sed -n 3p review/gates/gates.md
