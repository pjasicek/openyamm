#!/usr/bin/env bash
# Picked ladder candidate -> export/mm8_m456.glb: export_cand.py, swap_lod0.py into the installed file, LOD build
# (build_lods.py), knee rows (refine_knee_lods.py), variants on the LOD primitives (carry_variants.py), compaction.
# Usage: build_export.sh <ladder blend> <candidate, e.g. Cand_70>
set -euo pipefail
cd "$(dirname "$0")/.."
cp "work/$1" work/ladder.blend
REA_CAND=$2 REA_NODE=DragonHunter blender -b -P scripts/export_cand.py 2>&1 | grep EXPORTED
python3 scripts/swap_lod0.py work/mm8_m456_source_pre_reduce.glb work/cand_export.glb work/r76_lod0.glb DragonHunter | tail -1
blender -b -P scripts/build_lods.py 2>&1 | grep 'LOD triangles'
python3 scripts/refine_knee_lods.py work/r76_lods_raw.glb work/r76_lods.glb | python3 -c "import sys,ast; print('KNEE', [(x['mesh'], x['after']) for x in ast.literal_eval(sys.stdin.read().split('KNEE_LODS ', 1)[1])][::2])"
python3 scripts/carry_variants.py work/r76_lods.glb
python3 scripts/compact_glb.py work/r76_lods.glb
cp work/r76_lods.glb export/mm8_m456.glb
python3 ../../decorations/mm8_3d/animated/scripts/check_winding.py export/mm8_m456.glb | tail -1
