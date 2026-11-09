#!/usr/bin/env bash
set -euo pipefail
here="$(cd "$(dirname "$0")" && pwd)"
shared="$here/../../lod_repair_claude/scripts"
out=$1
shift
mkdir -p "$out"
python3 -I "$shared/lod_split.py" "$out" "$@" > /dev/null
stems=$(for g in "$@"; do basename "$g" .glb; done | paste -sd,)
timeout -k 5 180 /snap/blender/current/blender --background --factory-startup --threads 4 --python-exit-code 1 --python "$here/render_lods.py" -- "$out" "$stems" > "$out/render.log" 2>&1
python3 -I "$shared/lod_score.py" "$out" > "$out/scores.tsv"
