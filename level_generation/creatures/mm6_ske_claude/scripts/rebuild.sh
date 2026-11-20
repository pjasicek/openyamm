#!/usr/bin/env bash
# Replayable mesh + rig + clip chain for the MM6 skeleton (run from the project directory).
#   parts (examine_parts.py) -> build_rig -> add_skull -> reduce -> uv_ske -> add_eyes -> fist_sword -> retarget_fbx -> build_clips
set -euo pipefail
cd "$(dirname "$0")/.."
B=/snap/bin/blender
run() { "$B" --background --python "$@" 2>&1 | grep -E '^(JOINT|TRIS|EYE|SKULL|PIECE|LAYOUT|DENSITY|GRIP|FINGER|THUMB|SWORD|RETARGET|CLIP)|Error|rror' | grep -v '^JOINT' || true; }
run scripts/build_rig.py -- work/st_v1_parts.blend work/rig_v0.blend
run scripts/add_skull.py -- work/skull_v1_parts.blend work/rig_v0.blend work/rig_v0s.blend
run scripts/reduce.py -- work/rig_v0s.blend work/rig_v0r.blend
run scripts/uv_ske.py -- work/rig_v0r.blend work/rig_v0u.blend
run scripts/add_eyes.py -- work/rig_v0u.blend work/rig_v0e.blend
run scripts/fist_sword.py -- work/rig_v0e.blend work/rig_v1.blend
cp work/rig_v1.blend work/rig_v2.blend
M=mixamo/pack
run scripts/retarget_fbx.py -- work/rig_v2.blend "$M/sword and shield idle (4).fbx:Standing" \
    "$M/sword and shield walk.fbx:Walking" "$M/sword and shield run.fbx:Running" "$M/sword and shield slash.fbx:Attack" \
    "$M/sword and shield impact (3).fbx:Hit3" "$M/sword and shield death.fbx:Death" "$M/sword and shield idle.fbx:Fidget"
run scripts/build_clips.py -- work/rig_v2.blend work/rig_v3.blend
