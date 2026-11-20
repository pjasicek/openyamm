#!/usr/bin/env bash
# Picked ladder candidate (work/ladder_C.blend, Cand_35: 5,223 triangles) -> export/mm7_m386.glb: export the skinned
# candidate, swap it into the unreduced source GLB's LOD0, protect the floor contacts of every clip, rebuild LOD1-3
# and shadow LODs, shrink the shadow LODs, carry the tier variants to every LOD, winding check, viewer tiers.
# Usage: build_export.sh LEASE_TOKEN
set -euo pipefail
token=${1:?Usage: build_export.sh LEASE_TOKEN}
cd "$(dirname "$0")/.."; project=level_generation/creatures/mm7_m386_v2_claude
B() { (cd ../../.. && tools/run_creature_blender.sh --token "$token" "$project/scripts/$1") | tail -1; }
D=$PWD; G=(python3 ../../../tools/creature_workspace.py run --project . --token "$token" --)
cp work/ladder_C.blend work/ladder.blend
REA_CAND=Cand_35 REA_NODE=Robot B export_cand.py
"${G[@]}" python3 $D/scripts/swap_lod0.py $D/work/mm7_m386_source.glb $D/work/cand_export.glb $D/work/r35_lod0.glb Robot
REA_NODE=Robot B floor_contacts.py
B lod_chain.py
"${G[@]}" python3 $D/scripts/shrink_shadow_lods.py $D/work/r35_lods.glb $D/export/mm7_m386.glb
rm -f work/r35_lods.geometry.glb
"${G[@]}" python3 $D/scripts/carry_variants.py $D/export/mm7_m386.glb
python3 ../../decorations/mm8_3d/animated/scripts/check_winding.py export/mm7_m386.glb
"${G[@]}" python3 $D/scripts/viewer_tiers.py $D/export/mm7_m386.glb
