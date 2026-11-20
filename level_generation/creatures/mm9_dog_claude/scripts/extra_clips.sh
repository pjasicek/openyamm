#!/usr/bin/env bash
# Dropped MM9 clips (run2-clips-groupC, 2026-10-31): build the MM9 clips the accepted export left out with this
# project's own clips_mm9.py (scripts/extra_clips_blend.py on work/uv_v2.blend, the blend build_export.py opens), graft them into
# a copy of the accepted export, floor them with the passes build_runtime.sh gives accepted clips of the same kind, then
# graft only the new clips onto the accepted export with claude_shared/graft_clips.py, so meshes, LODs, variants and
# accepted clips stay byte for byte. Ctl_* controls go through the same steps and are compared with the installed clips.
# Written by claude_shared/make_extra_clips.py from scripts/extra_clips.json.
# The dog's build_export.py steps run on the new clips too (rest offsets, neck_spread). Floor as build_runtime.sh:
# the gaits ground-looped (sniffing and barking walks low-passed 0.02 s as Walking), the run away raised and low-passed
# 0.03 s as Running, the sitting loop ground-looped.
# Usage: TOK=<lease token> scripts/extra_clips.sh   (work/pre_clips_export.glb = the export before this step)
set -euo pipefail
cd "$(dirname "$0")/.."
here="$PWD"; repo="$(cd ../../.. && pwd)"; name=$(basename "$here" | sed 's/_claude$//')
G=../claude_shared/gltf_venv/bin/python; F=../claude_shared/floor/floor_fix.py; FS=scripts/floor_smooth.py
GR=../claude_shared/graft_clips.py
Q() { "$@" 2>&1 | grep -v "Unexpected value\|RuntimeWarning" ; }
E=${EXPORT:-work/pre_clips_export.glb}
(cd "$repo" && tools/run_creature_blender.sh --token "$TOK" level_generation/creatures/$(basename "$here")/scripts/extra_clips_blend.py \
  "$here/work/uv_v2.blend" "$here/work/extra_raw.glb" "$here/work/clips_extra.json" | tail -1)
Q $G $GR $E work/extra_raw.glb work/g0.glb --clip WalkSniff --clip WalkBark --clip RunAway --clip Sit --clip Ctl_Fidget --clip Ctl_Walking --clip Ctl_Running | tail -1
Q $G $F work/g0.glb work/gc.glb --ground-loop Ctl_Walking --ground-loop Ctl_Fidget --raise Ctl_Running --smooth-loop Ctl_Walking 0.02 --smooth-hold 0.5 --smooth-loop Ctl_Running 0.03 --smooth Ctl_Fidget 0.05 | tail -2
echo "control Ctl_Fidget vs Fidget"; Q $G ../claude_shared/compare_clips.py work/gc.glb Ctl_Fidget $E Fidget | tail -3
echo "control Ctl_Walking vs Walking"; Q $G ../claude_shared/compare_clips.py work/gc.glb Ctl_Walking $E Walking | tail -3
echo "control Ctl_Running vs Running"; Q $G ../claude_shared/compare_clips.py work/gc.glb Ctl_Running $E Running | tail -3
Q $G $F work/g0.glb work/gn.glb --ground-loop WalkSniff --ground-loop WalkBark --ground-loop Sit --raise RunAway --smooth-loop WalkSniff 0.02 --smooth-loop WalkBark 0.02 --smooth-hold 0.5 --smooth-loop RunAway 0.03 | tail -2
Q $G $GR $E work/gn.glb export/$name.glb --clip WalkSniff --clip WalkBark --clip RunAway --clip Sit | tail -1
Q $G ../claude_shared/graft_byte_check.py $E export/$name.glb
