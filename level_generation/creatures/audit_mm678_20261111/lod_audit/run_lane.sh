#!/usr/bin/env bash
# One audit lane: lod_split + lod_render (culled) per model, split GLBs deleted after rendering; scores later.
# Usage: run_lane.sh <after|before> <list of "stem<TAB>glb" lines>
set -uo pipefail
here=$(cd "$(dirname "$0")" && pwd); root=$(cd "$here/../../../.." && pwd)
scripts=$root/level_generation/creatures/lod_repair_claude/scripts
side=$1; list=$2; out=$here/$side; mkdir -p "$out"
while IFS=$'\t' read -r stem glb; do
  [ -z "$stem" ] && continue
  [ -f "$out/$stem/lod0_front.png" ] && continue
  python3 -I "$scripts/lod_split.py" "$out" "$root/$glb" > /dev/null || { echo "SPLITFAIL $stem"; continue; }
  [ -d "$out/$stem" ] || { echo "NOLODS $stem"; continue; }
  LOD_RENDER_CULL=1 blender -b -P "$scripts/lod_render.py" -- "$out" "$stem" > "$out/$stem/render.log" 2>&1
  rm -f "$out/$stem"/lod?.glb
  echo "DONE $stem"
done < "$list"
echo LANE_DONE
