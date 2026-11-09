#!/usr/bin/env bash
# m154 replayable chain (natm/bar1 route). Gate outputs printed; aborts on the first failure.
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
        grep -E '^(WALKBOB|STANCE|CONCAT|BOWFRAME|TRACKS|ARMCLEAR|SWORDCLEAR|CLEAN|GARMENT|RIG|HAND|WEIGHTS|RETARGET|TWIST|RULE|FINGERS|REDUCE|G4|G5|G6|GRIPSOLVE|GRIP|RUNFIT|FOOTLEVEL|ATTACK|BLENDS|LEGS|FEET|STEP|TIMING|FJ|FINGERFIT|THUMBCUT|HANDFRAME|KNUCKLE|SOLE|JERK)' "$log" | cut -c1-240 || true; }
W=$P/work
STAGE=${STAGE:-all}
if [ "$STAGE" = all ] || [ "$STAGE" = rig ]; then
run step1_clean.py $W/st_v1_parts.blend $W/step1.blend
run garments.py $W/step1.blend $W/step1.blend
ANKLE_FROM=${ANKLE_FROM:-} ELBOW_FROM=${ELBOW_FROM:-} WRIST_FROM=${WRIST_FROM:-} ELBOW_T=${ELBOW_T:-} python3 scripts/compose_joints.py | grep ELBOW
rm -f work/finger_joints.json
run build_rig.py
run fit_fingers.py $W/rig_v1.blend
run finger_joints.py $W/rig_v1.blend
run build_rig.py
run hand_frame_check.py $W/rig_v1.blend
fi
if [ "$STAGE" = all ] || [ "$STAGE" = anim ]; then
mapfile -t SETC < <(sed -e "s|\$L|$L|" "${SET_LIST:-scripts/set_clips.txt}" | grep -v '^#' | grep .)
mapfile -t MXC < <(sed -e "s|\$MX|$MX|" "${MX_LIST:-scripts/mx_clips.txt}" | grep -v '^#' | grep .)
run retarget.py $W/rig_v1.blend $W/rig_v2s.blend "$L/Armed.glb:ArmedIdle:GripRef" "${SETC[@]}"
run retarget_mixamo.py $W/rig_v2s.blend $W/rig_v2m.blend "${MXC[@]}"
run concat_actions.py $W/rig_v2m.blend $W/rig_v2k.blend Attack=Draw+Recoil
# the archer stands side-on (arrow and head ahead); the source's 0.9 m bow stance narrowed, legs by IK (m214 rule)
run bow_stance.py $W/rig_v2k.blend $W/rig_v2r.blend Attack
run run_fit.py $W/rig_v2r.blend $W/rig_v2f.blend
run foot_level.py $W/rig_v2f.blend $W/rig_v2.blend Standing Walking:const Hit Fidget FidgetFull Attack Death:until=${DEATH_UNTIL:-18} Running:rollonly
# blade out of the body where the source arms carry it through the legs (grip_pose.json from the previous grip solve)
[ -f work/grip_pose.json ] && run sword_clear.py $W/rig_v2.blend $W/rig_v2c.blend Fidget FidgetFull Death Running Hit Attack Walking Standing || cp $W/rig_v2.blend $W/rig_v2c.blend
FA=0.6 FA_RAMP=0.15,0.85 run twist_bones.py $W/rig_v2c.blend $W/rig_v2t.blend
run weights_fix.py $W/rig_v2t.blend $W/rig_v3.blend
SMOOTH_PASSES=${SMOOTH_PASSES:-3} run finger_weights.py $W/rig_v3.blend $W/rig_v4f.blend
run reduce_rigged.py $W/rig_v4f.blend $W/rig_v4.blend
SPREAD_MAX=${SPREAD_MAX:-60} GRIP_TILT=0 R_HANDLE=${R_HANDLE:-0.015} run grip_solve.py $W/rig_v4.blend GripRef 8
THUMB_CURL=${THUMB_CURL:-${LEFT_CURL:-1}} LEFT_CURL=${LEFT_CURL:-1} run apply_grip.py $W/rig_v4.blend $W/rig_v5g.blend
RELEASE_S=${RELEASE_S:-1.0667} LEAD=${LEAD:-0.15} run clip_timing.py $W/rig_v5g.blend $W/rig_v5t.blend
# walk bob: periodic smoothing of the pelvis height, both steps alike, legs re-solved to the same ankle paths (review 2026-10-20)
run walk_bob.py $W/rig_v5t.blend $W/rig_v5t.blend
# the timing blends from/to Standing swing the blade through the legs (attack recovery, fidget start): clear again,
# then re-bake the twist bones from the changed hand
# the bulky legs and tabard take hands the source swung past a slimmer body: swing the upper arm out the least, then
# clear the blade (after the arm, which can push the blade back in), then re-bake the twist bones
run arm_clear.py $W/rig_v5t.blend $W/rig_v5a.blend ${ARM_CLEAR:-Walking:L Walking:R Attack:L Death:R}   # m154: the draw anchor sat 6 cm inside the bulky head; swung out to the cheek
run sword_clear.py $W/rig_v5a.blend $W/rig_v5b.blend Attack Fidget Hit
MAX_TURN=${DEATH_MAX_TURN:-75} run sword_clear.py $W/rig_v5b.blend $W/rig_v5c.blend Death
FA=0.6 run rebake_twist.py $W/rig_v5c.blend $W/rig_v5w.blend Attack Fidget Hit Death Walking
# m154: bow, string and arrow bones and their tracks (release = Recoil frame 1)
run bow_tracks.py $W/rig_v5w.blend $W/rig_v5.blend
fi
