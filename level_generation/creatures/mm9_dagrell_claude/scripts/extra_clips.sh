#!/usr/bin/env bash
# Dropped MM9 clips (run2-clips-groupC, 2026-10-31): build the MM9 clips the accepted export left out with this
# project's own clips_mm9.py (scripts/extra_clips_blend.py on work/uv_v8.blend, the blend build_export.py opens), graft
# them into a copy of the accepted export, floor them as build_runtime.sh floors the accepted clips (ground-loop for the
# idles, crouch loops and the second walk, raise for the rest), then graft only the new clips onto the accepted export
# with claude_shared/graft_clips.py, so meshes, LODs, variants and accepted clips stay byte for byte. Ctl_* controls
# (Fidget1, Walk, HAttack1) go through the same steps and are compared with the installed clips.
# Usage: TOK=<lease token> scripts/extra_clips.sh   (work/pre_clips_export.glb = the export before this step)
set -euo pipefail
cd "$(dirname "$0")/.."
here="$PWD"; repo="$(cd ../../.. && pwd)"; name=mm9_dagrell
G=../claude_shared/gltf_venv/bin/python; F=../claude_shared/floor/floor_fix.py; GR=../claude_shared/graft_clips.py
Q() { "$@" 2>&1 | grep -v "Unexpected value\|RuntimeWarning" ; }
E=${EXPORT:-work/pre_clips_export.glb}
# MM9's Taunt carries exactly RAttack1's keys (= the accepted AttackRanged): bound as taunt: AttackRanged, not grafted
NEW=(CrouchedAware Crouch CrouchFidget ReturnToCrouch Walk2 Search AttackMelee2 Jump Hit2)
GROUND=(CrouchedAware Crouch CrouchFidget ReturnToCrouch Walk2 Search Ctl_Fidget Ctl_Walking)
RAISE=(AttackMelee2 Jump Hit2 Ctl_AttackMelee)
CTL=(Ctl_Fidget:Fidget Ctl_Walking:Walking Ctl_AttackMelee:AttackMelee)
(cd "$repo" && tools/run_creature_blender.sh --token "$TOK" level_generation/creatures/$(basename "$here")/scripts/extra_clips_blend.py \
  "$here/work/uv_v8.blend" "$here/work/extra_raw.glb" "$here/work/clips_extra.json" | tail -1)
Q $G $GR $E work/extra_raw.glb work/g0.glb $(for c in "${NEW[@]}" Ctl_Fidget Ctl_Walking Ctl_AttackMelee; do echo --clip $c; done) | tail -1
Q $G $F work/g0.glb work/g1.glb $(for c in "${GROUND[@]}"; do echo --ground-loop $c; done) $(for c in "${RAISE[@]}"; do echo --raise $c; done) | tail -1
for p in "${CTL[@]}"; do echo "control ${p%%:*} vs ${p##*:}"; Q $G ../claude_shared/compare_clips.py work/g1.glb ${p%%:*} $E ${p##*:} | tail -3; done
Q $G $GR $E work/g1.glb export/$name.glb $(for c in "${NEW[@]}"; do echo --clip $c; done) | tail -1
Q $G ../claude_shared/graft_byte_check.py $E export/$name.glb
