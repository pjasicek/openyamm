#!/usr/bin/env bash
# Everything after the paid paint: finish -> export -> MM9 clips -> finger keys -> runtime. Usage: TOKEN=<lease> scripts/rebuild.sh [--install]
set -euo pipefail
here="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"; repo="$(cd -- "$here/../../.." && pwd)"; cd "$here"
rel=level_generation/creatures/$(basename "$here"); G="$repo/level_generation/creatures/claude_shared/gltf_venv/bin/python"
B() { local out log; out=$(cd "$repo" && tools/run_creature_blender.sh --token "$TOKEN" "$@" 2>&1) || true
      log=$(echo "$out" | grep -o '/tmp/openyamm-creature-blender-[A-Za-z0-9]*\.log' | head -1)
      if grep -q "Error: script failed\|Traceback" "$log"; then grep -A12 Traceback "$log" | tail -14; echo "STEP FAILED: $1"; exit 1; fi
      grep -E "^(SKIRT|SPIKES|LINING|HIP|SCIMITAR|FACES|THUMB|LIFT|EXPORTED|DUMP)" "$log" | cut -c1-200 || true; }
B "$rel/scripts/finish_skelwar.py" "$here/work/uv_v2.blend" "$here/work/final_v2.blend" "$here/work/hand_poses.json"
B "$rel/scripts/dump_faces.py" "$here/work/final_v2.blend" "$here/work/faces.npz"
"$G" scripts/tone_skelwar.py | tail -3
"$G" scripts/tier_ramps.py | tail -2 | cut -c1-100
B "$rel/scripts/export_skelwar.py" "$here/work/final_v2.blend" "$here/work/skelwar_body_tex.glb"
"$G" scripts/clips_mm9.py work/skelwar_body_tex.glb work/skelwar_clips_raw.glb scripts/roles_skelwar_raw.json work/clips_raw.json | tail -1 | cut -c1-200
"$G" scripts/clips_mm9.py work/skelwar_body_tex.glb work/skelwar_clips.glb scripts/roles_skelwar.json work/clips.json | tail -1 | cut -c1-200
"$G" scripts/finger_keys.py work/skelwar_clips.glb work/skelwar_fingers.glb work/hand_poses.json | tail -1
"$G" scripts/skirt_keys.py work/skelwar_fingers.glb work/before_skirt/final_clips.glb work/skelwar_final_clips.glb work/skirt_keys.json | grep -E "^(CLIP|SKIRT)" | cut -c1-180
scripts/build_runtime.sh "$@"
