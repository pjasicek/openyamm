#!/usr/bin/env bash
# Dropped MM9 clips (run2-clips-groupC, 2026-10-31): build the MM9 clips the accepted export left out with this
# project's own clips_mm9.py (scripts/extra_clips_blend.py on work/uv_pod_v3.blend, the blend build_export.py opens), graft them into
# a copy of the accepted export, floor them with the passes build_runtime.sh gives accepted clips of the same kind, then
# graft only the new clips onto the accepted export with claude_shared/graft_clips.py, so meshes, LODs, variants and
# accepted clips stay byte for byte. Ctl_* controls go through the same steps and are compared with the installed clips.
# Written by claude_shared/make_extra_clips.py from scripts/extra_clips.json.
# Floor as build_runtime.sh pod: gaits ground-looped, taunt and hit raised. projectile (the pod in flight, MM9 plays
# it while the pod is a missile) is only raised (never under the floor); land ground-looped.
# Usage: TOK=<lease token> scripts/extra_clips_pod.sh   (work/pre_clips_export_pod.glb = the export before this step)
set -euo pipefail
cd "$(dirname "$0")/.."
here="$PWD"; repo="$(cd ../../.. && pwd)"; name=mm9_lobberpod
G=../claude_shared/gltf_venv/bin/python; F=../claude_shared/floor/floor_fix.py; FS=scripts/floor_smooth.py
GR=../claude_shared/graft_clips.py
Q() { "$@" 2>&1 | grep -v "Unexpected value\|RuntimeWarning" ; }
E=${EXPORT:-work/pre_clips_export_pod.glb}
(cd "$repo" && tools/run_creature_blender.sh --token "$TOK" level_generation/creatures/$(basename "$here")/scripts/extra_clips_blend_pod.py \
  "$here/work/uv_pod_v3.blend" "$here/work/extra_raw.glb" "$here/work/clips_extra.json" | tail -1)
Q $G $GR $E work/extra_raw.glb work/g0.glb --clip Projectile --clip Land --clip Taunt --clip Hit2 --clip Backpedal --clip BackpedalRun --clip Ctl_Fidget --clip Ctl_Walking --clip Ctl_Hit | tail -1
Q $G $F work/g0.glb work/gc.glb --ground-loop Ctl_Fidget --ground-loop Ctl_Walking --raise Ctl_Hit | tail -2
echo "control Ctl_Fidget vs Fidget"; Q $G ../claude_shared/compare_clips.py work/gc.glb Ctl_Fidget $E Fidget | tail -3
echo "control Ctl_Walking vs Walking"; Q $G ../claude_shared/compare_clips.py work/gc.glb Ctl_Walking $E Walking | tail -3
echo "control Ctl_Hit vs Hit"; Q $G ../claude_shared/compare_clips.py work/gc.glb Ctl_Hit $E Hit | tail -3
Q $G $F work/g0.glb work/gn.glb --ground-loop Backpedal --ground-loop BackpedalRun --ground-loop Land --raise Taunt --raise Hit2 --raise Projectile | tail -2
Q $G $GR $E work/gn.glb export/$name.glb --clip Projectile --clip Land --clip Taunt --clip Hit2 --clip Backpedal --clip BackpedalRun | tail -1
Q $G ../claude_shared/graft_byte_check.py $E export/$name.glb
