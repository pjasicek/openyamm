#!/usr/bin/env bash
# Picked candidate (work/ladder_k3.blend, Cand_45) -> export/mm7_m166.glb: export the skinned candidate, swap it into
# the unreduced source GLB's LOD0, protect the Death/Dead floor contacts, rebuild LOD1-3 and shadow LODs, shrink the
# shadow LODs (beholder project's script, <= 1 mm), carry the tier variants to every LOD, winding check.
set -euo pipefail
cd "$(dirname "$0")/.."; B=../mm7_m166_claude
cp work/ladder_k3.blend work/ladder.blend
REA_CAND=Cand_45 REA_NODE=Beholder blender -b --factory-startup -P scripts/export_cand.py 2>&1 | grep EXPORTED
python3 scripts/swap_lod0.py work/mm7_m166_source.glb work/cand_export.glb work/r45_lod0.glb Beholder
REA_NODE=Beholder blender -b --factory-startup -P scripts/floor_contacts.py 2>&1 | grep CONTACTS
blender -b --factory-startup -P scripts/build_lods.py 2>&1 | grep -i "lod tri"
python3 $B/scripts/shrink_shadow_lods.py work/r45_lods.glb export/mm7_m166.glb
rm -f work/r45_lods.geometry.glb
python3 scripts/carry_variants.py export/mm7_m166.glb
python3 ../../decorations/mm8_3d/animated/scripts/check_winding.py export/mm7_m166.glb
