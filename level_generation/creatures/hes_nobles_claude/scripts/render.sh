#!/usr/bin/env bash
# render.sh <blend> <out.png> <specs...>  (env VIEWS, RES, HIDE, ENGINE as render_pose.py)
set -e
H="$(cd "$(dirname "$0")" && pwd)"
timeout 900 /snap/blender/current/blender --background --factory-startup -noaudio --python "$H/render_pose.py" -- "$@" 2>&1 | grep -E "RENDERED|Error" || true
python3 "$H/sheet.py" "$2"
