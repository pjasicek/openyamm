#!/usr/bin/env bash
# Everything after the paid paint: finish -> export -> MM9 clips -> finger keys. Usage: TOKEN=<lease> scripts/rebuild.sh <uv blend> [--install]
set -euo pipefail
here="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"; repo="$(cd -- "$here/../../.." && pwd)"; cd "$here"
rel=level_generation/creatures/$(basename "$here"); G="$repo/level_generation/creatures/claude_shared/gltf_venv/bin/python"
UVB=$1; shift
B() { local out log; out=$(cd "$repo" && tools/run_creature_blender.sh --token "$TOKEN" "$@" 2>&1) || true
      log=$(echo "$out" | grep -o '/tmp/openyamm-creature-blender-[A-Za-z0-9]*\.log' | head -1)
      if grep -q "Error: script failed\|Traceback" "$log"; then grep -A12 Traceback "$log" | tail -14; echo "STEP FAILED: $1"; exit 1; fi
      grep -E "^(LINING|SCIMITAR|FACES|THUMB|FIST|GRIP|SPIKES|DARK|LIFT|EXPORTED|DUMP)" "$log" | cut -c1-200 || true; }
B "$rel/scripts/finish_skel.py" "$here/work/$UVB" "$here/work/final.blend" "$here/work/hand_poses.json"
B "$rel/scripts/dump_faces.py" "$here/work/final.blend" "$here/work/faces.npz"
if [ -f scripts/tone_skel.py ] && [ -f textures/skel_basecolor_graded.png ]; then "$G" scripts/tone_skel.py | tail -3; "$G" scripts/tier_ramps.py | tail -2 | cut -c1-120; fi
B "$rel/scripts/export_skel.py" "$here/work/final.blend" "$here/work/skel_body_tex.glb"
"$G" scripts/clips_mm9.py work/skel_body_tex.glb work/skel_clips_raw.glb scripts/roles_skel_raw.json work/clips_raw.json 2>&1 | tail -1 | cut -c1-300
"$G" scripts/clips_mm9.py work/skel_body_tex.glb work/skel_clips.glb scripts/roles_skel.json work/clips.json 2>&1 | tail -1 | cut -c1-300
"$G" scripts/finger_keys.py work/skel_clips.glb work/skel_fingers.glb work/hand_poses.json 2>&1 | tail -1
B "$rel/scripts/dump_pid.py" "$here/work/final.blend" "$here/work/pid_dump.npz"
"$G" scripts/arm_clear.py work/skel_fingers.glb work/skel_final_clips.glb --side L=' L ' --side R=' R ' --test arm --max-deg 24 --max-depth 0.035 --solids work/pid_dump.npz,1.1193,3+65+1003+1065+36+18 2>&1 | grep -E 'ARMCLEAR|Error|Trace' | cut -c1-200
