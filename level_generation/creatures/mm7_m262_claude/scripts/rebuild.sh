#!/usr/bin/env bash
# m262 replayable chain (from mm7_m150_claude) (copied from mm7_m406_claude, natm/bar1 route). Gate outputs printed; aborts on the first failure.
# STAGE=rig: cleanup -> garments -> joints -> rig + fingers;  STAGE=anim: clips -> run fit -> feet -> twist -> weights
# -> fingers -> reduction -> grip -> timing.  Uses tools/run_creature_blender.sh (TOKEN = the workspace lease).
set -euo pipefail
cd "$(dirname "$0")/.."
P=$(pwd)
. scripts/libpath.sh
: "${TOKEN:?set TOKEN to the workspace lease token}"
run() { local s=$1; shift; local out log
        out=$(cd "$P/../../.." && "$P/scripts/cap.sh" tools/run_creature_blender.sh --token "$TOKEN" "level_generation/creatures/$(basename "$P")/scripts/$s" "$@" 2>&1) || true
        log=$(echo "$out" | grep -o '/tmp/openyamm-creature-blender-[A-Za-z0-9]*\.log' | head -1)
        if grep -q "Error: script failed\|Traceback" "$log"; then grep -A12 Traceback "$log" | tail -14; echo "STEP FAILED: $s"; exit 1; fi
        grep -E '^(FLIGHTBLEND|TAIL|WINGJOIN|BIRDLEG|HOVER|FLIGHT|CARRY|WING|DEATHWINGS|ARMCLEAR|SWORDCLEAR|CLEAN|GARMENT|RIG|HAND|WEIGHTS|RETARGET|TWIST|RULE|FINGERS|REDUCE|G4|G5|G6|GRIPSOLVE|GRIP|RUNFIT|FOOTLEVEL|ATTACK|BLENDS|LEGS|FEET|STEP|TIMING|FJ|FINGERFIT|THUMBCUT|HANDFRAME|KNUCKLE|SOLE|JERK)' "$log" | cut -c1-240 || true; }
W=$P/work
STAGE=${STAGE:-all}
if [ "$STAGE" = all ] || [ "$STAGE" = rig ]; then
run step1_clean.py $W/st_v1_parts.blend $W/step1.blend
run garments.py $W/step1.blend $W/step1.blend
ELBOW_FROM=${ELBOW_FROM:-} WRIST_FROM=${WRIST_FROM:-} ELBOW_T=${ELBOW_T:-} scripts/cap.sh python3 scripts/compose_joints.py | grep ELBOW
# m262: bird legs (hip, hidden knee, hock, ball) instead of Meshy's human knee/ankle
run leg_joints.py $W/step1.blend
rm -f work/finger_joints.json
run build_rig.py
THUMB_MIN_CUT=${THUMB_MIN_CUT:-0.03} THUMB_NEAR=${THUMB_NEAR:-0.10} run fit_fingers.py $W/rig_v1.blend
run finger_joints.py $W/rig_v1.blend
run build_rig.py
run hand_frame_check.py $W/rig_v1.blend
fi
if [ "$STAGE" = all ] || [ "$STAGE" = anim ]; then
mapfile -t SETC < <(sed -e "s|\$L|$L|" "${SET_LIST:-scripts/set_clips.txt}" | grep -v '^#' | grep .)
mapfile -t MXC < <(sed -e "s|\$MX|$MX|" "${MX_LIST:-scripts/mx_clips.txt}" | grep -v '^#' | grep .)
run retarget.py $W/rig_v1.blend $W/rig_v2s.blend "$L/Armed.glb:ArmedIdle:GripRef" "${SETC[@]}"
run retarget_mixamo.py $W/rig_v2s.blend $W/rig_v2r.blend "${MXC[@]}"
# m262: no run fit or foot levelling (bird feet, she never stands; hover_legs.py replaces the legs)
cp $W/rig_v2r.blend $W/rig_v2f.blend
cp $W/rig_v2f.blend $W/rig_v2k.blend
cp $W/rig_v2k.blend $W/rig_v2.blend
# blade out of the body where the source arms carry it through the legs (grip_pose.json from the previous grip solve)
[ -f work/grip_pose.json ] && run sword_clear.py $W/rig_v2.blend $W/rig_v2c.blend Fidget FidgetFull Death Running Hit Attack AttackFull Walking Standing || cp $W/rig_v2.blend $W/rig_v2c.blend
FA=0.6 FA_RAMP=0.15,0.85 run twist_bones.py $W/rig_v2c.blend $W/rig_v2t.blend
run weights_fix.py $W/rig_v2t.blend $W/rig_v3.blend
SMOOTH_PASSES=${SMOOTH_PASSES:-3} run finger_weights.py $W/rig_v3.blend $W/rig_v4f.blend
run reduce_rigged.py $W/rig_v4f.blend $W/rig_v4.blend
SPREAD_MAX=${SPREAD_MAX:-60} GRIP_TILT=0 R_HANDLE=${R_HANDLE:-0.015} run grip_solve.py $W/rig_v4.blend GripRef 8
THUMB_CURL=${THUMB_CURL:-${LEFT_CURL:-1}} LEFT_CURL=${LEFT_CURL:-1} run apply_grip.py $W/rig_v4.blend $W/rig_v5g.blend
LEAD=${LEAD:-0.15} run clip_timing.py $W/rig_v5g.blend $W/rig_v5t.blend
# the timing blends from/to Standing swing the blade through the legs (attack recovery, fidget start): clear again,
# then re-bake the twist bones from the changed hand
# the bulky legs and tabard take hands the source swung past a slimmer body: swing the upper arm out the least, then
# clear the blade (after the arm, which can push the blade back in), then re-bake the twist bones
run arm_clear.py $W/rig_v5t.blend $W/rig_v5a.blend ${ARM_CLEAR:-Walking:L Walking:R Attack:L Death:R}
run sword_clear.py $W/rig_v5a.blend $W/rig_v5b.blend Attack Fidget Hit
MAX_TURN=${DEATH_MAX_TURN:-45} run sword_clear.py $W/rig_v5b.blend $W/rig_v5c.blend Death
FA=0.6 run rebake_twist.py $W/rig_v5c.blend $W/rig_v5.blend Attack Fidget Hit Death Walking Standing
fi
if [ "$STAGE" = all ] || [ "$STAGE" = wings ]; then
# m262: tail bone, hover (flight loop as Walking, bird legs on every clip), knife carried before the body in the
# flight, wing chains and their motion, wings joined into the body
run tail_rig.py $W/rig_v5.blend $W/rig_v5t.blend
IMPACT=${IMPACT:-0.983} run hover.py $W/rig_v5t.blend $W/rig_h1.blend
CARRY_JSON=$P/scripts/carry_flight.json run author_carry.py $W/rig_h1.blend $W/rig_h2.blend Walking:0.0
FA=0.6 run rebake_twist.py $W/rig_h2.blend $W/rig_h3f.blend Walking
run flight_blend.py $W/rig_h3f.blend $W/rig_h3g.blend
# the raised legs meet the falling right arm and knife in the death: swing the arm out, turn the knife clear, rebake
run arm_clear.py $W/rig_h3g.blend $W/rig_h3a.blend Death:R Death:L Attack:R
BLADE_TIP=0.31 MAX_TURN=60 run sword_clear.py $W/rig_h3a.blend $W/rig_h3c.blend Death Attack Hit Walking
FA=0.6 run rebake_twist.py $W/rig_h3c.blend $W/rig_h3.blend Death Attack Hit Walking
ROOT_X=0.12 SHOULDER_X=0.35 WRIST_FRAC=0.62 run wings_rig.py $W/rig_h3.blend $W/rig_w1.blend
DEATH_ELEVS=-80,-60,-40,-20,0 REST_ELEV=0 FLAP_MID=-37 FLAP_AMP=55 ATT_UP=12 ATT_DOWN=-55 HIT_UP=-30 IMPACT=${IMPACT:-0.983} run wings_anim.py $W/rig_w1.blend $W/rig_w2.blend
WING_TRIS=${WING_TRIS:-1900} run wings_join.py $W/rig_w2.blend $W/rig_v5x.blend
fi
