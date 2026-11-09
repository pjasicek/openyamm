#!/usr/bin/env bash
# Candidate -> $E/mm9_skelwar.glb, after the creature's own runtime chain (../mm9_skeletonwarrior_claude/scripts/build_runtime.sh:
# prepare -> build_actor_lods (defaults 0.5/0.18/0.06, 4 influences) -> shrink_shadow_lods -> region variants -> floor ->
# emission): export_cand (linings back as reversed copies of every lined face, kept or reduced, on each set's dark texel;
# floor = source's lowest point) -> swap_lod0 into the installed source (materials, tier variants, region masks, eye emission,
# floor- and skirt-fixed clips stay byte for byte; the scimitar primitive kept whole) -> keep_normals (installed normals on
# vertices used only by kept faces) -> build_lods.py (tools/build_actor_lods.py defaults, 4 influences, soles and crown
# protected) -> shrink_shadow_lods -> fix_lod_winding -> carry_variants -> keep_lod3 (the installed LOD3 and its shadow: every rebuild lost the thighs) -> winding check.
# Usage (project folder): LADDER=<label> EXPORT=export_x scripts/build_export.sh <tag>   (work/ladder_<LADDER>.blend holds Cand_<tag>)
set -euo pipefail
cd "$(dirname "$0")/.."; tag=$1; E=${EXPORT:-export}; mkdir -p $E; n=mm9_skelwar
repo=/home/pjasicek/github/OpenYAMM; G="scripts/cap.sh $repo/level_generation/creatures/claude_shared/gltf_venv/bin/python -I"
BL="scripts/cap.sh /snap/bin/blender --background --factory-startup --threads 4 --python-exit-code 1"
cp work/ladder_${LADDER}.blend work/ladder.blend
REA_TAG=$tag REA_CAND=Cand_$tag REA_NODE=SkelWar $BL -P scripts/export_cand.py 2>&1 | grep -E "LINING|FLOOR|EXPORTED|Error"
DROP_ATTRS=COLOR_0,COLOR_1 KEEP_PRIMS=Scimitar $G scripts/swap_lod0.py before/$n.glb work/cand_export.glb $E/${n}_lod0.glb SkelWar 2>&1 | grep -v prefix
$G scripts/keep_normals.py work/source_nolining.glb $E/${n}_lod0.glb work/keep_r$tag.npy 2>&1 | grep -v prefix
$BL --disable-autoexec --python scripts/build_lods.py -- "$PWD/$E/${n}_lod0.glb" "$PWD/$E/${n}_lods.glb" SkelWar 2>&1 </dev/null | grep -E "PROTECT|LOD triangles|Error"
$G scripts/shrink_shadow_lods.py $E/${n}_lods.glb $E/${n}_shadow.glb SkelWar 2>&1 | grep -v prefix | tail -1 | cut -c1-160
$G scripts/fix_lod_winding.py $E/${n}_shadow.glb $E/$n.glb 2>&1 | grep -v prefix
$G scripts/carry_variants.py $E/$n.glb 2>&1 | grep -v prefix
$G scripts/keep_lod3.py before/$n.glb $E/$n.glb 2>&1 | grep -v prefix
for f in $E/${n}_lods.geometry.glb $E/${n}_shadow.glb $E/${n}_lods.glb; do if [[ -f $f ]]; then rm $f; fi; done
$G "$repo/level_generation/decorations/mm8_3d/animated/scripts/check_winding.py" $E/$n.glb 2>&1 | grep -v prefix | tail -3
