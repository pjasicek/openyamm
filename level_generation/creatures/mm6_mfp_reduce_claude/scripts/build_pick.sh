#!/usr/bin/env bash
# Build one ladder step as a full runtime candidate (reduce_installed.sh build steps): export/mm6_mfp_<label><tag>.glb
# with LODs and variants, viewer GLBs per variant, close renders. Usage: build_pick.sh r55 [ladder label]
set -euo pipefail
tag=$1; label=${2:-}; P="$(cd "$(dirname "$0")/.." && pwd)"; ROOT="$(cd "$P/../../.." && pwd)"; cd "$P"
[ -z "$label" ] || cp "work/ladder_$label.blend" work/ladder.blend
out=$label$tag
glb="$P/work/mm6_mfp_r3_stab3.glb"  # round-3 runtime export with the new Attack (wrist-capped stab)
REA_INFLUENCES=8 REA_CAND=Cand_${tag#r} REA_NODE=PeasantF3 blender -b -P scripts/export_cand.py > work/export_cand_$out.log 2>&1
python3 scripts/swap_lod0.py "$glb" work/cand_export.glb export/mm6_mfp_${out}_lod0.glb PeasantF3
blender -b -P "$ROOT/tools/build_actor_lods.py" -- export/mm6_mfp_${out}_lod0.glb export/mm6_mfp_$out.glb --mesh-node PeasantF3 2>&1 | grep "LOD tri"
python3 scripts/carry_variants.py export/mm6_mfp_$out.glb
python3 scripts/viewer_variants.py export/mm6_mfp_$out.glb $out > /dev/null
first=$(ls review/viewer | grep -m1 "_$out.glb")
blender -b -P scripts/close_views.py -- review/viewer/$first $out > work/close_$out.log 2>&1
