#!/usr/bin/env bash
# Candidate -> export/<out>.glb with the Clan Soldier's own LOD chain (../mm9_clansoldier_claude/scripts/rebuild.sh after the clips):
# export_cand (floor = source's lowest point; REA_RELINE rebuilds the skirt lining from the reduced skirt) -> swap_lod0 into the
# installed source (materials, variants, clips stay byte for byte) -> fix_normals (installed normals on source vertices, the rule on
# new ones; KEEP_PRIMS restored byte for byte) -> tools/build_actor_lods.py (4 influences) -> shrink_shadow_lods -> carry_variants
# -> fix_winding -> check_winding.
# Usage (project folder): REA_BLEND=ladder_a.blend REA_RELINE=work/drop_a.npy scripts/build_export.sh Cand_73 <out name>
set -euo pipefail
cd "$(dirname "$0")/.."; cand=$1; n=$2
repo=/home/pjasicek/github/OpenYAMM; G="scripts/cap.sh $repo/level_generation/creatures/claude_shared/gltf_venv/bin/python"
BL="scripts/cap.sh /snap/bin/blender --background --factory-startup --threads 4 --python-exit-code 1"
REA_CAND=$cand REA_NODE=ClanSoldier $BL -P scripts/export_cand.py 2>&1 | grep -E "FLOOR|RELINED|EXPORTED|Error"
$G scripts/swap_lod0.py before/mm9_clansoldier.glb work/cand_export.glb work/${n}_swap.glb ClanSoldier 2>&1 | grep -v frozen
KEEP_PRIMS=${KEEP_PRIMS-ClanWeapon_A} $G scripts/fix_normals.py before/mm9_clansoldier.glb work/${n}_swap.glb export/${n}_lod0.glb ClanSoldier 2>&1 | grep -v frozen
$BL --disable-autoexec --python "$repo/tools/build_actor_lods.py" -- "$PWD/export/${n}_lod0.glb" "$PWD/export/${n}_lods.glb" --mesh-node ClanSoldier --max-influences 4 2>&1 </dev/null | grep -E "LOD triangles|Error"
$G scripts/shrink_shadow_lods.py export/${n}_lods.glb work/${n}_shadow.glb ClanSoldier 2>&1 | grep -v frozen | tail -1 | cut -c1-160
$G scripts/carry_variants.py work/${n}_shadow.glb 2>&1 | grep -v frozen
$G scripts/fix_winding.py work/${n}_shadow.glb export/${n}.glb 2>&1 | grep -v frozen | tail -1 | cut -c1-160
if [[ -f export/${n}_lods.geometry.glb ]]; then rm export/${n}_lods.geometry.glb; fi
$G "$repo/level_generation/decorations/mm8_3d/animated/scripts/check_winding.py" export/${n}.glb 2>&1 | grep -v frozen | tail -1
ls -la export/${n}.glb
