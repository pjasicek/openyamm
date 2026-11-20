#!/usr/bin/env bash
# Ladder step -> teeth rebuild -> LOD0 GLB in the fixed-texture source -> viewer GLBs -> mouth and whole renders.
# Usage: build_teeth_cand.sh <step, e.g. 50>   (needs work/ladder.blend from run_ladder.sh and work/full_fixed.glb)
set -euo pipefail; cd "$(dirname "$0")/.."; p=$1
REA_CAND=Cand_$p blender -b -P scripts/fix_teeth.py 2>&1 | grep -E "^TRIS"
REA_BLEND=teeth.blend REA_CAND=Cand_teeth REA_NODE=Eye blender -b -P scripts/export_cand.py > work/export_cand_t$p.log 2>&1
python3 scripts/swap_lod0.py work/full_fixed.glb work/cand_export.glb work/t${p}_lod0.glb Eye | tail -1
python3 scripts/viewer_variants.py work/t${p}_lod0.glb t$p > /dev/null
blender -b -P scripts/mouth_views.py -- review/viewer/mm6_bh_a_t$p.glb review/mouth/t$p > /dev/null 2>&1
blender -b -P scripts/close_views.py -- review/viewer/mm6_bh_a_t$p.glb t$p > /dev/null 2>&1
