#!/usr/bin/env bash
# Picked candidate -> export/mm8_m440.glb: export_cand (Cand_67 of work/ladder.blend = ladder_i) -> swap_lod0 ->
# build_lods -> preserve_contacts (LOD0 right hand and feet in every LOD, as production) -> shrink_shadow_lods (the
# m440 project's shadow tuck, contacts excluded) -> carry_variants.
set -euo pipefail; cd "$(dirname "$0")/.."
REA_CAND=Cand_67 REA_NODE=M440 blender -b -P scripts/export_cand.py 2>&1 | grep EXPORTED
python3 scripts/swap_lod0.py work/mm8_m440_source_pre_reduce.glb work/cand_export.glb work/r67_lod0.glb M440
blender -b -P scripts/build_lods.py 2>&1 | grep -E "PROTECTED|LOD triangles|Error" || true
python3 scripts/preserve_contacts.py export/mm8_m440_lods.glb export/mm8_m440_lods_contacts.glb
python3 scripts/shrink_shadow_lods.py export/mm8_m440_lods_contacts.glb export/mm8_m440_lods_shadowfix.glb
cp export/mm8_m440_lods_shadowfix.glb export/mm8_m440.glb; python3 scripts/carry_variants.py export/mm8_m440.glb
