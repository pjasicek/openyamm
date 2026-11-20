#!/usr/bin/env bash
# m442 replayable chain (natm/bar1 route; goblin peasant woman with a sickle, no attack, no run). Gate outputs printed; aborts on the first failure.
# STAGE=rig: cleanup -> garments -> joints -> rig + fingers;  STAGE=anim: clips -> run fit -> feet -> twist -> weights
# -> fingers -> reduction -> grip -> timing.  Uses tools/run_creature_blender.sh (TOKEN = the workspace lease).
set -euo pipefail
cd "$(dirname "$0")/.."
P=$(pwd)
. scripts/libpath.sh
: "${TOKEN:?set TOKEN to the workspace lease token}"
run() { local s=$1; shift; local out log
        out=$(cd "$P/../../.." && tools/run_creature_blender.sh --token "$TOKEN" "level_generation/creatures/$(basename "$P")/scripts/$s" "$@" 2>&1) || true
        log=$(echo "$out" | grep -o '/tmp/openyamm-creature-blender-[A-Za-z0-9]*\.log' | head -1)
        if grep -q "Error: script failed\|Traceback" "$log"; then grep -A12 Traceback "$log" | tail -14; echo "STEP FAILED: $s"; exit 1; fi
        grep -E '^(WALKBOB|SWORDCLEAR|CLEAN|GARMENT|RIG|HAND|WEIGHTS|RETARGET|TWIST|RULE|FINGERS|REDUCE|G4|G5|G6|GRIPSOLVE|GRIP|RUNFIT|FOOTLEVEL|ATTACK|BLENDS|LEGS|FEET|STEP|TIMING|CARRY|FJ|FINGERFIT|THUMBCUT|HANDFRAME|KNUCKLE|SOLE|JERK)' "$log" | cut -c1-240 || true; }
W=$P/work
STAGE=${STAGE:-all}
if [ "$STAGE" = all ] || [ "$STAGE" = rig ]; then
run step1_clean.py $W/st_v1_parts.blend $W/step1.blend
run garments.py $W/step1.blend $W/step1.blend
ELBOW_T=${ELBOW_T:-} python3 scripts/compose_joints.py | grep ELBOW
rm -f work/finger_joints.json
run build_rig.py
run fit_fingers.py $W/rig_v1.blend
run finger_joints.py $W/rig_v1.blend
run build_rig.py
run hand_frame_check.py $W/rig_v1.blend
fi
if [ "$STAGE" = all ] || [ "$STAGE" = anim ]; then
# m442 (goblin peasant woman with a sickle): no attack (the native attack reuses the walk), no run (speed 140)
mapfile -t MXC < <(sed -e "s|\$MX|$MX|" "${MX_LIST:-scripts/mx_clips.txt}" | grep -v '^#' | grep .)
run retarget.py $W/rig_v1.blend $W/rig_v2s.blend "$L/Armed.glb:ArmedIdle:GripRef"
run retarget_mixamo.py $W/rig_v2s.blend $W/rig_v2r.blend "${MXC[@]}"
run abduct_arms.py $W/rig_v2r.blend $W/rig_v2a0.blend Standing Walking   # wide sleeves clear the thighs
ARM_ABDUCT_DEG=14 run abduct_arms.py $W/rig_v2a0.blend $W/rig_v2a.blend Fidget   # Look Around brings the sickle arm in
run foot_level.py $W/rig_v2a.blend $W/rig_v2.blend Standing Walking:const Hit Fidget Death:until=${DEATH_UNTIL:-12}
# user review 2026-10-20: the sickle hand was rolled palm-forward (the idle's forearm roll). Batch J's goblin carry
# (mm7_7m452_claude, carry.json): wrist beside the right hip, the handle forward, 6 deg out and 10 deg down in the pelvis
# frame, hand roll by least wrist strain -> the palm faces the body
[ -f work/grip_pose.json ] && PALM_IN=1 SIDE=R run author_carry.py $W/rig_v2.blend $W/rig_v2.blend ${CARRY_CLIPS:-Standing:0.3 Walking:0.3 Fidget:0.3}
# blade out of the body where the source arms carry it through the legs (grip_pose.json from the previous grip solve)
[ -f work/grip_pose.json ] && run sword_clear.py $W/rig_v2.blend $W/rig_v2c.blend Fidget Death Hit Walking Standing || cp $W/rig_v2.blend $W/rig_v2c.blend
FA=0.6 FA_RAMP=0.15,0.85 run twist_bones.py $W/rig_v2c.blend $W/rig_v2t.blend
run weights_fix.py $W/rig_v2t.blend $W/rig_v3.blend
SMOOTH_PASSES=${SMOOTH_PASSES:-6} run finger_weights.py $W/rig_v3.blend $W/rig_v4f.blend
run reduce_rigged.py $W/rig_v4f.blend $W/rig_v4.blend
# user review 2026-10-20 (the handle lay outside the fist): grip_solve.py takes the palm side from the source fist's
# curl (the A-pose fingertips were level with the knuckles and the old test put the handle on the BACK of the hand);
# the thumb closes over the index finger's middle phalanx (THUMB_TARGET=index), the knuckle segment is not pulled onto
# the handle (FIST_PULL_FROM=1)
GRIP_TILT=0 R_HANDLE=${R_HANDLE:-0.014} run grip_solve.py $W/rig_v4.blend GripRef 8
LEFT_CURL=${LEFT_CURL:-0.55} run apply_grip.py $W/rig_v4.blend $W/rig_v5g.blend
run clip_timing.py $W/rig_v5g.blend $W/rig_v5t.blend
run walk_bob.py $W/rig_v5t.blend $W/rig_v5t.blend        # batch A/J walk fix: even pelvis bob, legs re-solved
run sword_clear.py $W/rig_v5t.blend $W/rig_v5c.blend Fidget Hit Death
FA=0.6 run rebake_twist.py $W/rig_v5c.blend $W/rig_v5.blend Fidget Hit Death
fi
