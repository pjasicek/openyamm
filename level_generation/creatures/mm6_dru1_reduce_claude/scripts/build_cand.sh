#!/usr/bin/env bash
# One ladder step -> full runtime candidate export/mm6_dru1_<label>.glb (LODs, shadow LODs, variant mappings),
# viewer GLBs per tier and close renders. Usage: build_cand.sh <ladder label> <rNN>
set -euo pipefail
label=$1; tag=$2; P="$(cd "$(dirname "$0")/.." && pwd)"; ROOT="$(cd "$P/../../.." && pwd)"; cd "$P"
out=$label$tag; glb="$ROOT/assets_source/worlds/mm6/models/mm6_dru1.glb"
cp work/ladder_$label.blend work/ladder.blend
REA_CAND=Cand_${tag#r} REA_NODE=Druidess blender -b -P scripts/export_cand.py 2>&1 | grep -E "EXPORTED|NORMALS|Error"
python3 scripts/swap_lod0.py "$glb" work/cand_export.glb export/mm6_dru1_${out}_lod0.glb Druidess
blender -b -P "$ROOT/tools/build_actor_lods.py" -- export/mm6_dru1_${out}_lod0.glb export/mm6_dru1_${out}_lods.glb --mesh-node Druidess 2>&1 | grep "LOD tri"
python3 ../mm6_dru1_claude/scripts/shrink_shadow_lods.py export/mm6_dru1_${out}_lods.glb export/mm6_dru1_$out.glb > /dev/null
rm -f export/mm6_dru1_${out}_lods.glb export/mm6_dru1_${out}_lods.geometry.glb
python3 scripts/carry_variants.py export/mm6_dru1_$out.glb
python3 scripts/viewer_variants.py export/mm6_dru1_$out.glb $out > /dev/null
REA_FACING=-Y blender -b -P scripts/close_views.py -- review/viewer/$(ls review/viewer | grep -m1 "_$out.glb") $out > work/close_$out.log 2>&1
