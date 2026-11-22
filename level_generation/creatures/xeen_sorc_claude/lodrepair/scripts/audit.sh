#!/usr/bin/env bash
# Render every LOD of the given GLBs (standing pose, front/three-quarter/side) and score each LOD switch at its
# switch size. Usage: audit.sh <audit dir> <glb...>  -> <audit dir>/<stem>/lod<N>_<view>.png, <audit dir>/scores.tsv
set -euo pipefail
here=$(cd "$(dirname "$0")" && pwd); out=$1; shift; mkdir -p "$out"
python3 -I "$here/lod_split.py" "$out" "$@" > /dev/null
stems=$(for g in "$@"; do basename "$g" .glb; done | paste -sd,)
repo=$(cd "$here/../../../../.." && pwd)
# Blender only under the project lease and through lane S's Blender wrapper (one Blender at a time in the lane)
(cd "$repo" && python3 tools/creature_workspace.py run --project level_generation/creatures/xeen_sorc_claude --token "$TOK" -- \
  level_generation/creatures/xeen_tiers_claude/bin/blender --background --factory-startup --disable-autoexec --threads 4 \
  --python-exit-code 1 --python level_generation/creatures/xeen_sorc_claude/lodrepair/scripts/lod_render.py -- "$out" "$stems") > "$out/render.log" 2>&1
python3 -I "$here/lod_score.py" "$out" > "$out/scores.tsv"
