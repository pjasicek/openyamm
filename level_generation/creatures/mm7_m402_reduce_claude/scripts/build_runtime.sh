#!/usr/bin/env bash
# Reduced Spider runtime GLB from Cand_50 of work/ladder_d3.blend: export_cand (fringe cards re-rigged on their legs,
# smooth shading; REA_FLAT=1 for the original flat shading) -> swap_lod0 into the rollback source (materials, colour
# variants, clips byte for byte) -> build_lods (0.5 / 0.25 / 0.12, protected extremes and floor contacts) ->
# shrink_shadow_lods (as the original build) -> carry_variants (LOD and shadow primitives).
# Output: export/mm7_m402.glb (smooth) or, with REA_FLAT=1, work/mm7_m402_flat.glb. NO install.
# Usage: [REA_FLAT=1] scripts/build_runtime.sh
set -euo pipefail
cd "$(dirname "$0")/.."
out=export/mm7_m402.glb; [ "${REA_FLAT:-0}" = 1 ] && out=work/mm7_m402_flat.glb
cp work/ladder_d3.blend work/ladder.blend
REA_FIX_CARDS=1 REA_CAND=Cand_50 REA_NODE=M402 blender -b -P scripts/export_cand.py 2>&1 | grep -E "EXPORTED|Error"
python3 scripts/swap_lod0.py work/mm7_m402_source_pre_reduce.glb work/cand_export.glb work/pick_lod0.glb M402
blender -b -P scripts/build_lods.py 2>&1 | grep -E "PROTECTED|LOD tri|Error"
python3 scripts/shrink_shadow_lods.py work/pick_lods.glb "$out" > /dev/null
python3 scripts/carry_variants.py "$out"
ls -la "$out"
echo "install later with: python3 tools/install_model.py level_generation/creatures/mm7_m402_reduce_claude/export/mm7_m402.glb --world mm7"
