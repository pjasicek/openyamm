#!/usr/bin/env bash
# Build one ladder step as a full runtime candidate (reduce_installed.sh build steps, 8 influences):
# export/mm6_nobl_<label><tag>.glb with LODs and variants, viewer GLBs per variant, close renders.
# Usage: build_pick.sh r45 [ladder label: work/ladder_<label>.blend]
set -euo pipefail
tag=$1; label=${2:-}; P="$(cd "$(dirname "$0")/.." && pwd)"; ROOT="$(cd "$P/../../.." && pwd)"; cd "$P"
[ -z "$label" ] || cp "work/ladder_$label.blend" work/ladder.blend
out=$label$tag
glb="$ROOT/assets_source/worlds/mm6/models/mm6_nobl.glb"
REA_CAND=Cand_${tag#r} REA_NODE=Swordsman blender -b -P scripts/export_cand.py > work/export_cand_$out.log 2>&1
python3 scripts/swap_lod0.py "$glb" work/cand_export.glb export/mm6_nobl_${out}_lod0.glb Swordsman
blender -b -P "$ROOT/tools/build_actor_lods.py" -- export/mm6_nobl_${out}_lod0.glb export/mm6_nobl_$out.glb --mesh-node Swordsman 2>&1 | grep "LOD tri"
python3 scripts/carry_variants.py export/mm6_nobl_$out.glb
python3 scripts/viewer_variants.py export/mm6_nobl_$out.glb $out > /dev/null
REA_FACING=-Y blender -b -P scripts/close_views.py -- review/viewer/mm6_nobl_a_$out.glb $out > work/close_$out.log 2>&1
