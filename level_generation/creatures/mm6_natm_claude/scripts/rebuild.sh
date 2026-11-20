#!/usr/bin/env bash
# natm replayable chain (adapted from mm6_gob2_claude / mm6_bar1_claude). Gate outputs printed; aborts on the first failure.
set -euo pipefail
cd "$(dirname "$0")/.."
. scripts/libpath.sh
B=/snap/bin/blender
run() { local log; log=$("$B" --background --factory-startup --threads 4 --python-exit-code 1 --python "$@" 2>&1) || { echo "$log" | tail -20; echo "STEP FAILED: $1"; exit 1; }
        echo "$log" | grep -E '^(CLEAN|FINGERSMOOTH|FINGERPIECES|HANDSTRETCH|SUBDIV|KNUCKLE|ARM|ANKLE|REDUCE|RIG|HAND|WEIGHTS|RETARGET|TWIST|RULE|FINGERS|G4|G5|G6|GRIPSOLVE|GRIP|CARRY|RUNFIT|FOOTLEVEL|SPEARCLEAR|HEAD|ATTACK|ARM|FJ|FINGERFIT|THUMBCUT|HANDFRAME|SPEAR|SHIELD|CLIP|TIMING)|Error|rror' | cut -c1-240 || true; }
STAGE=${STAGE:-all}
if [ "$STAGE" = all ] || [ "$STAGE" = rig ]; then
run scripts/step1_clean.py -- work/st_v1_parts.blend work/step1.blend
run scripts/garments.py -- work/step1.blend work/step1.blend
python3 scripts/compose_joints.py | grep ELBOW
rm -f work/finger_joints.json
run scripts/build_rig.py
run scripts/fit_fingers.py -- work/rig_v1.blend
run scripts/finger_joints.py -- work/rig_v1.blend
run scripts/build_rig.py
run scripts/hand_frame_check.py -- work/rig_v1.blend
fi
if [ "$STAGE" = all ] || [ "$STAGE" = anim ]; then
# clip lists: one <file>:<clip>:<Action> per line ($L / $MX expanded); Mixamo names contain spaces
mapfile -t SETC < <(sed -e "s|\$L|$L|" "${SET_LIST:-scripts/set_clips.txt}" | grep -v '^#' | grep .)
mapfile -t MXC < <(sed -e "s|\$MX|$MX|" "${MX_LIST:-scripts/mx_clips.txt}" | grep -v '^#' | grep .)
run scripts/retarget.py -- work/rig_v1.blend work/rig_v2s.blend "$L/Armed.glb:ArmedIdle:GripRef" "${SETC[@]}"
run scripts/retarget_mixamo.py -- work/rig_v2s.blend work/rig_v2r.blend "${MXC[@]}"
# spear carry on the locomotion/idle/hit arms, then the authored attack over Stab2 (author_attack.py)
run scripts/run_fit.py -- work/rig_v2r.blend work/rig_v2f.blend
run scripts/foot_level.py -- work/rig_v2f.blend work/rig_v2l.blend Standing Walking:const Hit Cast Fidget Death:until=24
run scripts/author_carry.py -- work/rig_v2l.blend work/rig_v2c.blend Standing:0.3 Walking:0.3 Running:0.35:yaw=8:pitch=6 Hit:0.4
run scripts/author_attack.py -- work/rig_v2c.blend work/rig_v2a.blend
run scripts/spear_clear.py -- work/rig_v2a.blend work/rig_v2.blend Fidget Death Cast Hit Attack
FA=0.6 FA_RAMP=0.15,0.85 run scripts/twist_bones.py -- work/rig_v2.blend work/rig_v2t.blend
run scripts/weights_fix.py -- work/rig_v2t.blend work/rig_v3.blend
run scripts/finger_weights.py -- work/rig_v3.blend work/rig_v4f.blend
run scripts/reduce_rigged.py -- work/rig_v4f.blend work/rig_v4.blend
GRIP_TILT=0 R_HANDLE=0.015 run scripts/grip_solve.py -- work/rig_v4.blend GripRef 8
run scripts/apply_grip.py -- work/rig_v4.blend work/rig_v5g.blend
run scripts/clip_timing.py -- work/rig_v5g.blend work/rig_v5.blend
fi
