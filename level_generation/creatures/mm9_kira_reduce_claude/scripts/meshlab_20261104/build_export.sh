#!/usr/bin/env bash
# Reduced Kira runtime GLB from a ladder candidate, the installed chain's geometry steps only (mm9_kira_claude/scripts/rebuild.sh after
# prepare): export_cand.py -> swap_lod0.py (into the installed GLB: materials, ORM/class-map textures, clips with their floor pass, skin
# unchanged) -> tools/build_actor_lods.py (as installed: default ratios 0.5/0.18/0.06, 4 influences) -> Kira's
# shrink_shadow_lods.py -> fix_winding.py -> check_winding.py -> export/mm9_kira.glb. No floor_fix re-run: the clips stay byte-identical.
# Usage: scripts/build_export.sh <ladder blend> <Cand_NN>
set -euo pipefail
cd "$(dirname "$0")/.."; repo="$(cd ../../.. && pwd)"
G=../claude_shared/gltf_venv/bin/python; export PYTHONPATH=/usr/lib/python3/dist-packages
BL="scripts/cap.sh /snap/bin/blender --background --factory-startup --threads 4 --python-exit-code 1"
cp "$1" work/ladder.blend
REA_CAND=$2 REA_NODE=Kira $BL -P scripts/export_cand.py 2>&1 | grep -E "FLOOR|EXPORTED|Error"
scripts/cap.sh $G -W ignore scripts/swap_lod0.py before/mm9_kira.glb work/cand_export.glb work/pick_lod0.glb Kira
$BL --python "$repo/tools/build_actor_lods.py" -- "$PWD/work/pick_lod0.glb" "$PWD/work/pick_lods.glb" --mesh-node Kira --max-influences 4 2>&1 | grep -E "LOD triangles|Error"
scripts/cap.sh $G -W ignore scripts/shrink_shadow_lods.py work/pick_lods.glb work/pick_shadowfix.glb Kira | tail -1 | cut -c1-160
scripts/cap.sh $G -W ignore scripts/fix_winding.py work/pick_shadowfix.glb export/mm9_kira.glb | tail -1 | cut -c1-160
if [[ -e work/pick_lods.geometry.glb ]]; then rm work/pick_lods.geometry.glb; fi
$G -W ignore "$repo/level_generation/decorations/mm8_3d/animated/scripts/check_winding.py" export/mm9_kira.glb | tail -1
ls -la export/mm9_kira.glb
