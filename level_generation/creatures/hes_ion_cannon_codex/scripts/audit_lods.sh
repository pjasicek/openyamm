#!/usr/bin/env bash
set -euo pipefail
own=$(cd "$(dirname "$0")" && pwd)
here=$(cd "$own/../../lod_repair_claude/scripts" && pwd)
out=$1
shift
mkdir -p "$out"
python3 -B "$here/lod_split.py" "$out" "$@" > /dev/null
stems=$(for glb in "$@"; do basename "$glb" .glb; done | paste -sd,)
timeout --kill-after=15s 600 /snap/blender/current/blender -noaudio --background --factory-startup \
  --disable-autoexec --threads 4 --python-exit-code 1 --python "$own/lod_render.py" \
  -- "$out" "$stems" > "$out/render.log" 2>&1
python3 -B "$here/lod_score.py" "$out" > "$out/scores.tsv"
