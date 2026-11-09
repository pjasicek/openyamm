#!/usr/bin/env bash
# Replayable chain from the cleaned mesh to the gated rig (goblin; adapted from mm6_bar1_claude). Gate outputs printed.
#   step1.blend + meshy rig -> arm_rings (joints) -> build_rig (frames, mesh-measured hands, mesh-fitted fingers)
#   -> retarget (world copy) -> twist_bones -> weights_fix -> finger_weights -> reduce -> grip -> G4/G6
set -euo pipefail
cd "$(dirname "$0")/.."
. scripts/libpath.sh
B=/snap/bin/blender
# a failing step must stop the chain (a crash once let every later gate run on a stale file)
run() { local log; log=$("$B" --background --python-exit-code 1 --python "$@" 2>&1) || { echo "$log" | tail -20; echo "STEP FAILED: $1"; exit 1; }
        echo "$log" | grep -E '^(FINGERSMOOTH|FINGERPIECES|HANDSTRETCH|SUBDIV|KNUCKLE|ARM|ANKLE|REDUCE|RIG|HAND|WEIGHTS|RETARGET|TWIST|RULE|FINGERS|G4|G6|GRIPSOLVE|GRIP|FJ|FINGERFIT|THUMBCUT|HANDFRAME)|Error|rror' | cut -c1-220 || true; }
run scripts/step1_clean.py -- work/st_v1_parts.blend work/step1.blend
run scripts/arm_rings.py -- work/step1.blend
rm -f work/finger_joints.json
run scripts/build_rig.py
run scripts/fit_fingers.py -- work/rig_v1.blend
run scripts/finger_joints.py -- work/rig_v1.blend
run scripts/build_rig.py
run scripts/hand_frame_check.py -- work/rig_v1.blend
run scripts/retarget.py -- work/rig_v1.blend work/rig_v2a.blend "$L/Armed.glb:ArmedIdle:Standing" \
    "$L/Armed.glb:ArmedGetHitF1:Hit" "$L/Armed.glb:ArmedDeath1:Death" \
    "$L/Armed.glb:ArmedCastLAttack1:Cast" "$L/1Hand.glb:SwordAttackR6:Attack"
# G2/G6: upper arms 1.35x and hips 1.26x the source's -> the swinging hands hit the pouch and skirt strips in the
# walk/run; a constant upper-arm abduction for the locomotion clips only (the attack and the rest stay exact copies)
ARM_ABDUCT_DEG=${LOCO_ABDUCT:-7} run scripts/retarget.py -- work/rig_v2a.blend work/rig_v2.blend "$L/Armed.glb:ArmedWalk:Walking" \
    "$L/Armed.glb:ArmedRunForward:Running"
run scripts/twist_bones.py -- work/rig_v2.blend work/rig_v2t.blend
run scripts/weights_fix.py -- work/rig_v2t.blend work/rig_v3.blend
run scripts/finger_weights.py -- work/rig_v3.blend work/rig_v4f.blend
run scripts/reduce_rigged.py -- work/rig_v4f.blend work/rig_v4r.blend
run scripts/subdivide_fingers.py -- work/rig_v4r.blend work/rig_v4.blend
[ "${STOP_AFTER_REDUCE:-}" ] && exit 0
run scripts/grip_solve.py -- work/rig_v4.blend Standing 8
run scripts/apply_grip.py -- work/rig_v4.blend work/rig_v5.blend
run scripts/g4_weights.py -- work/rig_v4.blend v4 ${G4_POSES:-Standing:0 Walking:6 Running:6 Attack:4 Attack:7 Attack:9 Attack:12 Cast:12 Hit:6 Death:20}
run scripts/g6_contacts.py -- work/rig_v5.blend Standing Walking Running Attack Hit Cast Death
run scripts/g5_hand_stretch.py -- work/rig_v5.blend Standing:0 Walking Attack Cast
