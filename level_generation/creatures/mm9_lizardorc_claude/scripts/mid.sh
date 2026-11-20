#!/usr/bin/env bash
# rebuild.sh up to work/final_clips.glb (no LODs, no install), for gate iteration. Project folder.
set -euo pipefail
here="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"; repo="$(cd -- "$here/../../.." && pwd)"; cd "$here"
. scripts/env.sh
n=mm9_lizardorc; L=../claude_shared
BUMPS=${BUMPS:-$(cat scripts/bumps.txt 2>/dev/null || true)}
"$G" scripts/weights_liz.py work/heat2.npz work/w2.npz 2>&1 | grep -E 'influences|Error|Trace' | cut -c1-120
"$G" scripts/assemble.py work/joined.npz work/w2.npz work/uv.npz work/final.npz work/final_w.npz scripts/tex_final.json 2>&1 | tail -1
"$G" scripts/build_glb.py work/final.npz work/final_w.npz work/body.glb 2>&1 | tail -1
"$G" scripts/clips_mm9.py work/body.glb work/raw_clips.glb scripts/roles_liz.json work/clips.json 2>&1 | tail -1 | cut -c1-80
"$G" scripts/finger_keys.py work/raw_clips.glb work/fist_clips.glb 2>&1 | tail -1
"$G" scripts/half_keys.py work/fist_clips.glb work/ref_half.glb 2>&1 | tail -1 | cut -c1-100
if [[ -z "${SKIPBUMP:-}" && -n "$BUMPS" ]]; then
  "$G" scripts/half_keys.py work/fist_clips.glb work/raw_half.glb 2>&1 | tail -1 | cut -c1-140
  "$G" scripts/arm_bump.py work/raw_half.glb work/bump_clips.glb $BUMPS 2>&1 | grep -E 'BUMP|Traceback|Error' | cut -c1-140
else cp work/fist_clips.glb work/bump_clips.glb; fi
"$G" scripts/tip_lift.py work/bump_clips.glb work/tip_clips.glb AttackMelee:R 2>&1 | grep -E 'TIP|Traceback|Error' | cut -c1-160
"$G" scripts/half_keys.py work/tip_clips.glb work/half_clips.glb 2>&1 | grep -E 'HALF|Traceback|Error' | cut -c1-140
"$G" scripts/flap_solve.py work/half_clips.glb work/final_clips.glb 2>&1 | grep -E "^[A-Z]" | cut -c1-200
