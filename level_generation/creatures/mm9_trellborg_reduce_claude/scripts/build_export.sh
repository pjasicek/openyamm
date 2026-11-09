#!/usr/bin/env bash
# Candidate -> export/<out>.glb with the Trellborg's own LOD chain (../mm9_trellborg_claude/scripts/rebuild.sh after the clips):
# export_cand (floor = source's lowest point) -> swap_lod0 into the installed source (materials, variants, clips stay byte for byte)
# -> fix_normals (installed normals on source vertices, Blender's export normals on new ones; the club restored byte for byte) ->
# club_rebuild (CLUB=1: 10-sided lathe on the same cylinder UVs, nails byte for byte) -> build_lods.py (tools/build_actor_lods.py, 4 influences, hair tops and soles protected)
# -> shrink_shadow_lods -> carry_variants -> fix_winding -> check_winding.
# Usage (project folder): REA_BLEND=ladder_a.blend [CLUB=1] scripts/build_export.sh Cand_80 <out name>
set -euo pipefail
cd "$(dirname "$0")/.."; cand=$1; n=$2
repo=/home/pjasicek/github/OpenYAMM; G="scripts/cap.sh $repo/level_generation/creatures/claude_shared/gltf_venv/bin/python"
BL="scripts/cap.sh /snap/bin/blender --background --factory-startup --threads 4 --python-exit-code 1"
REA_CAND=$cand REA_NODE=Trellborg $BL -P scripts/export_cand.py 2>&1 | grep -E "FLOOR|RELINED|EXPORTED|Error"
$G scripts/swap_lod0.py before/mm9_trellborg.glb work/cand_export.glb work/${n}_swap.glb Trellborg 2>&1 | grep -v frozen
KEEP_PRIMS=${KEEP_PRIMS-TrellborgClub} $G scripts/fix_normals.py before/mm9_trellborg.glb work/${n}_swap.glb export/${n}_lod0.glb Trellborg 2>&1 | grep -v frozen
if [[ "${CLUB:-0}" == 1 ]]; then $G scripts/club_rebuild.py export/${n}_lod0.glb export/${n}_lod0.glb 2>&1 | grep -v frozen; fi
$G scripts/death_floor_pts.py export/${n}_lod0.glb work/${n}_deathpts.npy 2>&1 | grep DEATHFLOOR
DEATH_PTS=$PWD/work/${n}_deathpts.npy $BL --disable-autoexec --python scripts/build_lods.py -- "$PWD/export/${n}_lod0.glb" "$PWD/export/${n}_lods.glb" Trellborg 2>&1 </dev/null | grep -E "PROTECT|LOD triangles|Error"
$G scripts/shrink_shadow_lods.py export/${n}_lods.glb work/${n}_shadow.glb Trellborg 2>&1 | grep -v frozen | tail -1 | cut -c1-160
$G scripts/carry_variants.py work/${n}_shadow.glb 2>&1 | grep -v frozen
$G scripts/fix_winding.py work/${n}_shadow.glb export/${n}.glb 2>&1 | grep -v frozen | tail -1 | cut -c1-160
if [[ -f export/${n}_lods.geometry.glb ]]; then rm export/${n}_lods.geometry.glb; fi
$G "$repo/level_generation/decorations/mm8_3d/animated/scripts/check_winding.py" export/${n}.glb 2>&1 | grep -v frozen | tail -1
ls -la export/${n}.glb
