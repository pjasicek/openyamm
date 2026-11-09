#!/usr/bin/env bash
# Picked candidate (work/ladder_uni.blend, Cand_40) -> export/mm7_m158.glb: export the skinned candidate, swap it into
# the unreduced source GLB's LOD0, protect the Death/Dead floor contacts, rebuild LOD1-3 and shadow LODs, shrink the
# shadow LODs, carry the tier variants to every LOD, winding check.
set -euo pipefail
cd "$(dirname "$0")/.."; B=../mm7_m158_claude
cp work/ladder_uni.blend work/ladder.blend
REA_CAND=Cand_40 REA_NODE=Bat blender -b --factory-startup -P scripts/export_cand.py 2>&1 | grep EXPORTED
python3 scripts/swap_lod0.py work/mm7_m158_source.glb work/cand_export.glb work/r40_lod0.glb Bat
REA_NODE=Bat blender -b --factory-startup -P scripts/floor_contacts.py 2>&1 | grep CONTACTS
blender -b --factory-startup -P scripts/build_lods.py 2>&1 | grep -i "lod tri"
python3 $B/scripts/shrink_shadow_lods.py work/r40_lods.glb export/mm7_m158.glb
rm -f work/r40_lods.geometry.glb
python3 scripts/carry_variants.py export/mm7_m158.glb
python3 ../../decorations/mm8_3d/animated/scripts/check_winding.py export/mm7_m158.glb
