#!/usr/bin/env bash
# Dropped MM9 clips (run2-clips-groupC, 2026-10-31): build the MM9 clips the accepted export left out with this
# project's own clips_mm9.py (scripts/extra_clips_blend.py on the source blend build_export_v2.py opens), graft them
# into a copy of the accepted export, floor them as build_runtime.sh floors the accepted clips (standing lift 0.1648,
# tail lifted from its own joints, ground-loop for the backpedal, raise for the rest), then graft only the new clips
# onto the accepted export with claude_shared/graft_clips.py, so meshes, LODs, materials and accepted clips stay byte
# for byte. Ctl_* controls (fidget1, walk, Hattack1) go through the same steps and are compared with the installed clips.
# Usage: TOK=<lease token> scripts/extra_clips.sh   (work/pre_clips_export.glb = the export before this step)
set -euo pipefail
cd "$(dirname "$0")/.."
here="$PWD"; repo="$(cd ../../.. && pwd)"; name=mm9_greaterdemon
G=../claude_shared/gltf_venv/bin/python; F=../claude_shared/floor/floor_fix.py; GR=../claude_shared/graft_clips.py
Q() { "$@" 2>&1 | grep -v "Unexpected value\|RuntimeWarning" ; }
E=${EXPORT:-work/pre_clips_export.glb}
NEW=(Spawn Taunt Fidget2 Block AttackMelee2 DodgeLeft DodgeRight Hit2 Backpedal BackpedalRun)
RAISE=(Spawn Taunt Fidget2 Block AttackMelee2 DodgeLeft DodgeRight Hit2 BackpedalRun Ctl_Fidget Ctl_AttackMelee)
CTL=(Ctl_Fidget:Fidget Ctl_Walking:Walking Ctl_AttackMelee:AttackMelee)
(cd "$repo" && tools/run_creature_blender.sh --token "$TOK" level_generation/creatures/$(basename "$here")/scripts/extra_clips_blend.py \
  "$here/work/uv_v2b.blend" "$here/work/extra_raw.glb" "$here/work/clips_extra.json" | tail -1)
Q $G $GR $E work/extra_raw.glb work/g0.glb $(for c in "${NEW[@]}" Ctl_Fidget Ctl_Walking Ctl_AttackMelee; do echo --clip $c; done) | tail -1
Q $G $F work/g0.glb work/g0h.glb --hover 0.164800 Death Dead | tail -1
Q $G $F work/g0h.glb work/g1.glb --lift-joints "${NEW[@]}" Ctl_Fidget Ctl_Walking Ctl_AttackMelee --lift-only 'Xtail*' \
  --ground-loop Backpedal --ground-loop Ctl_Walking $(for c in "${RAISE[@]}"; do echo --raise $c; done) | tail -1
for p in "${CTL[@]}"; do echo "control ${p%%:*} vs ${p##*:}"; Q $G ../claude_shared/compare_clips.py work/g1.glb ${p%%:*} $E ${p##*:} | tail -3; done
Q $G $GR $E work/g1.glb export/$name.glb $(for c in "${NEW[@]}"; do echo --clip $c; done) | tail -1
Q $G ../claude_shared/graft_byte_check.py $E export/$name.glb
