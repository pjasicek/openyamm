#!/usr/bin/env bash
# From the final UV blend: export -> runtime -> viewer GLB + manifest. Usage: rebuild_tail.sh <lease token> <uv blend name> <revision>
set -uo pipefail
T="$1"; UV="$2"; REV="$3"
cd "$(dirname "$0")/../../../.."
P=level_generation/creatures/mm9_fish_claude
out=$(tools/run_creature_blender.sh --token "$T" $P/scripts/build_export.py $P/work/$UV $P/work/anim_final.blend $P/export/mm9_fish_lod0.glb $P/work/clips_final.json)
log=${out#Blender log: }
grep -E "EXPORTED|Traceback" "$log" | cut -c1-140
python3 tools/creature_workspace.py run --project $P --token "$T" -- $P/scripts/build_runtime.sh 2>&1 | grep -E "lift|WINDING|LOD tri|Traceback|Error"
cd $P
cp export/mm9_fish.glb review/viewer/fish_a.glb
python3 scripts/make_viewer_manifest.py "$REV" "fish_a=Fish (MM9 227)=review/viewer/fish_a.glb" | cut -c1-100
