#!/usr/bin/env bash
# m150 replayable chain (copied from mm7_m406_claude, natm/bar1 route). Gate outputs printed; aborts on the first failure.
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
        grep -E '^(CLAVFIX|FLIGHT|CARRY|WING|DEATHWINGS|ARMCLEAR|SWORDCLEAR|CLEAN|GARMENT|RIG|HAND|WEIGHTS|RETARGET|TWIST|RULE|FINGERS|REDUCE|G4|G5|G6|GRIPSOLVE|GRIP|RUNFIT|FOOTLEVEL|ATTACK|BLENDS|LEGS|FEET|STEP|TIMING|FJ|FINGERFIT|THUMBCUT|HANDFRAME|KNUCKLE|SOLE|JERK)' "$log" | cut -c1-240 || true; }
W=$P/work
STAGE=${STAGE:-all}
if [ "$STAGE" = all ] || [ "$STAGE" = rig ]; then
run step1_clean.py $W/st_v2_parts.blend $W/step1.blend
run garments.py $W/step1.blend $W/step1.blend
FOOT_MIRROR=${FOOT_MIRROR:-} ELBOW_FROM=${ELBOW_FROM:-} WRIST_FROM=${WRIST_FROM:-} ELBOW_T=${ELBOW_T:-} python3 scripts/compose_joints.py | grep ELBOW
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
run run_fit.py $W/rig_v2r.blend $W/rig_v2f.blend
# m150 v5: the source idle/hit's rounded shoulders out (user review: slumped), the hit's head snap halved
run clavicle_fix.py $W/rig_v2f.blend $W/rig_v2p.blend Standing Walking Running Hit Fidget FidgetFull Death Attack:0.6 AttackFull:0.6
run foot_level.py $W/rig_v2p.blend $W/rig_v2k.blend Standing Walking:const Hit Fidget FidgetFull Attack AttackFull Death:until=${DEATH_UNTIL:-18} Running:rollonly
# m150: Standing holds the sword diagonally across the body as the native sa frames (before the timing blends, which
# ease every one-shot clip from and to Standing frame 0)
[ -f work/grip_pose.json ] && CARRY_JSON=$P/scripts/carry_stand.json run author_carry.py $W/rig_v2k.blend $W/rig_v2.blend Standing:0.3 || cp $W/rig_v2k.blend $W/rig_v2.blend
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
# m150: Walking = authored flight (the Mixamo walk was only a placeholder for the chain), sword aimed forward, then the
# wing chains and their motion on every clip
PITCH=${PITCH:-48} KNEE=${KNEE:-40} run author_flight.py $W/rig_v5.blend $W/rig_f1.blend
CARRY_JSON=$P/scripts/carry_flight.json run author_carry.py $W/rig_f1.blend $W/rig_f2.blend Walking:0.0
FA=0.6 run rebake_twist.py $W/rig_f2.blend $W/rig_f3.blend Walking
run wings_rig.py $W/rig_f3.blend $W/rig_w1.blend
IMPACT=${IMPACT:-0.983} run wings_anim.py $W/rig_w1.blend $W/rig_w2.blend
WING_TRIS=${WING_TRIS:-2200} run wings_join.py $W/rig_w2.blend $W/rig_v5x.blend
fi
