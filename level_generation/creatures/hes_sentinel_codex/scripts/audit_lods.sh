#!/usr/bin/env bash
# Render every LOD of the given GLBs (standing pose, front/three-quarter/side) and score each LOD switch at its
# switch size. Usage: audit.sh <audit dir> <glb...>  -> <audit dir>/<stem>/lod<N>_<view>.png, <audit dir>/scores.tsv
set -euo pipefail
here=$(cd "$(dirname "$0")/../../lod_repair_claude/scripts" && pwd); out=$1; shift; mkdir -p "$out"
python3 -I "$here/lod_split.py" "$out" "$@" > /dev/null
stems=$(for g in "$@"; do basename "$g" .glb; done | paste -sd,)
/snap/blender/current/blender -noaudio --background --factory-startup --disable-autoexec --threads 4 --python-exit-code 1 -P "$here/lod_render.py" --python-expr 'import sys,os;sys.stdout.flush();sys.stderr.flush();os._exit(0)' -- "$out" "$stems" > "$out/render.log" 2>&1
python3 -I "$here/lod_score.py" "$out" > "$out/scores.tsv"
