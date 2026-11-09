#!/usr/bin/env bash
# Staged export from the picked candidates: body Cand_82 of work/ladder_p.blend (rollers clamped, chest hole closed), rubble Cand_80 of
# rubble/work/ladder_u.blend -> export/mm8_m608.glb (LODs, variants, collapsed-mesh visibility, LOD normal repair).
set -euo pipefail; cd "$(dirname "$0")/.."; T=../../../tools
blender -b -P scripts/roller_clamp.py -- "$PWD/work/ladder_p.blend" Cand_82 | grep -E "CLAMPED"
blender -b -P scripts/patch_hole.py -- Cand_82 | grep PATCHED
REA_CAND=Cand_82 REA_NODE=Juggernaut REA_SHADE=angle:45 blender -b -P scripts/export_cand.py | grep EXPORTED
(cd rubble; cp work/ladder_u.blend work/ladder.blend
 REA_CAND=Cand_80 REA_NODE=Rubble REA_SHADE=flat blender -b -P scripts/export_cand.py | grep EXPORTED)
python3 scripts/swap_lod0.py work/mm8_m608_source_pre_reduce.glb work/cand_export.glb work/body_swapped.glb Juggernaut
python3 scripts/swap_lod0.py work/body_swapped.glb rubble/work/cand_export.glb work/r82_lod0.glb Rubble
blender -b -P scripts/rubble_contacts.py -- "$PWD/work/r82_lod0.glb" | grep CONTACTS
blender -b -P scripts/build_lods.py | grep "LOD tri"
cp work/m608_lods.glb export/mm8_m608.glb
python3 scripts/carry_variants.py export/mm8_m608.glb
python3 $T/model_hide_collapsed_meshes.py export/mm8_m608.glb --write export/mm8_m608.glb | tail -1
python3 scripts/fix_lod_normals.py export/mm8_m608.glb
python3 ../../decorations/mm8_3d/animated/scripts/check_winding.py export/mm8_m608.glb | tail -1
python3 scripts/compare_glb.py work/mm8_m608_source_pre_reduce.glb export/mm8_m608.glb
python3 scripts/shoulder_rules.py export/mm8_m608.glb
