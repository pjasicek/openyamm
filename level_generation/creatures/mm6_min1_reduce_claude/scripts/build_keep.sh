#!/usr/bin/env bash
# One ladder step as a runtime candidate with the installed LOD1-3 kept (REA_KEEP_LODS swap, no LOD rebuild):
# export/mm6_min1_<label><tag>.glb, viewer GLBs per variant. Usage: build_keep.sh r80 [ladder label]
set -euo pipefail
tag=$1; label=${2:-}; P="$(cd "$(dirname "$0")/.." && pwd)"; ROOT="$(cd "$P/../../.." && pwd)"; cd "$P"
[ -z "$label" ] || cp "work/ladder_$label.blend" work/ladder.blend
out=$label$tag
glb="$ROOT/assets_source/worlds/mm6/models/mm6_min1.glb"
REA_CAND=Cand_${tag#r} REA_INFLUENCES=8 REA_NODE=Minotaur blender -b -P scripts/export_cand.py > work/export_cand_$out.log 2>&1
REA_KEEP_LODS=1 python3 scripts/swap_lod0.py "$glb" work/cand_export.glb export/mm6_min1_$out.glb Minotaur
python3 scripts/viewer_variants.py export/mm6_min1_$out.glb $out > /dev/null
