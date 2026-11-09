#!/usr/bin/env bash
# m190 replayable chain (mm7_m222_claude's one-handed weapon route with mm7_m218_claude's side-aware grip scripts).
# Prints the gate lines; aborts on the first failure.
# STAGE=rig: cleanup -> joints -> source-frame rig -> fitted fingers; STAGE=anim: clips -> run fit -> feet -> twist ->
# weights -> fingers -> reduction -> grip -> timing -> axe clearance. Token: CREATURE_3D_TOKEN (the project lease).
set -euo pipefail
here="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
repo="$(cd -- "$here/../../.." && pwd)"
cd "$repo"
. "$here/scripts/libpath.sh"
P=level_generation/creatures/mm7_m190_claude; W="$repo/$P/work"
run() { local out log; out=$(tools/run_creature_blender.sh --token "$CREATURE_3D_TOKEN" "$P/scripts/$1" "${@:2}" 2>&1) || {
          log=$(echo "$out" | sed -n 's/^Blender log: //p'); tail -25 "$log"; echo "STEP FAILED: $1"; exit 1; }
        log=$(echo "$out" | sed -n 's/^Blender log: //p')
        grep -E '^(BOBSMOOTH|DESPIKE|CLEAN|JOINTS|SYMMETRY|RIG|HAND|WEIGHTS|THUMBCUT|THUMBWALK|KNUCKLE|FINGER|FINGERCUT|FJ|HANDFRAME|RETARGET|RUNFIT|FOOTLEVEL|SWORDCLEAR|ARMCLEAR|LOOPSEAM|CARRY|ATTACK|BLENDS|LEGS|FEET|STEP|IMPACT|TIMING|TWIST|GARMENT|RULE|REDUCE|HANDLE|GRIPSOLVE|GRIP )' "$log" | cut -c1-240 || true; }
STAGE=${STAGE:-all}
if [ "$STAGE" = all ] || [ "$STAGE" = rig ]; then
run step1_clean.py "$W/st_v1_parts.blend" "$W/step1.blend"
run joints_m190.py "$W/step1.blend"
run remove_finger.py "$W/step1.blend" "$W/step1.blend"     # six digits per hand -> thumb + four fingers
rm -f "$W/finger_joints.json"
run build_rig.py
HAND_PIECES=4,5 run fit_fingers.py "$W/rig_v1.blend"
run finger_joints.py "$W/rig_v1.blend"
run build_rig.py
run hand_frame_check.py "$W/rig_v1.blend"
fi
if [ "$STAGE" = all ] || [ "$STAGE" = anim ]; then
mapfile -t SETC < <(sed -e "s|\$L|$L|" "$here/scripts/set_clips.txt" | grep -v '^#' | grep .)
mapfile -t MXC < <(sed -e "s|\$MX|$MX|" "$here/scripts/mx_clips.txt" | grep -v '^#' | grep .)
run retarget.py "$W/rig_v1.blend" "$W/rig_v2s.blend" "$L/Armed.glb:ArmedIdle:GripRef" "${SETC[@]}"
run retarget_mixamo.py "$W/rig_v2s.blend" "$W/rig_v2r.blend" "${MXC[@]}"
run run_fit.py "$W/rig_v2r.blend" "$W/rig_v2f.blend"
run foot_level.py "$W/rig_v2f.blend" "$W/rig_v2.blend" Standing Walking:const Hit Fidget FidgetFull Attack AttackFull Death:until=${DEATH_UNTIL:-24} Running:rollonly
# the walk's pelvis hitch after each heel strike (source Walk) low-passed, legs re-solved to the same feet (user
# review 2026-10-20: the head went down, up, down)
run bob_smooth.py "$W/rig_v2.blend" "$W/rig_v2.blend" Walking
# the run's source arm swings the haft across the chest: authored carry (carry.json: axe up and forward at the side)
[ -f "$W/grip_pose.json" ] && SIDE=R run author_carry.py "$W/rig_v2.blend" "$W/rig_v2.blend" ${CARRY_CLIPS:-Running:0.25}
[ -f "$W/grip_pose.json" ] && run sword_clear.py "$W/rig_v2.blend" "$W/rig_v2c.blend" Fidget FidgetFull Death Running Hit Attack AttackFull Walking Standing || cp "$W/rig_v2.blend" "$W/rig_v2c.blend"
FA=0.6 FA_RAMP=0.15,0.85 run twist_bones.py "$W/rig_v2c.blend" "$W/rig_v2t.blend"
run weights_fix.py "$W/rig_v2t.blend" "$W/rig_v3.blend"
SMOOTH_PASSES=${SMOOTH_PASSES:-6} HAND_PIECES=4,5 run finger_weights.py "$W/rig_v3.blend" "$W/rig_v4f.blend"
run reduce_rigged.py "$W/rig_v4f.blend" "$W/rig_v4.blend"
SIDE=R run grip_from_source.py "$L/Armed.glb" ArmedIdle:8
THUMB_MAX=${THUMB_MAX:-30} GRIP_TILT=0 R_HANDLE=${R_HANDLE:-0.016} run grip_solve.py "$W/rig_v4.blend" GripRef 8
run apply_grip.py "$W/rig_v4.blend" "$W/rig_v5g.blend"
LEAD=${LEAD:-0.3} run clip_timing.py "$W/rig_v5g.blend" "$W/rig_v5t.blend"
run sword_clear.py "$W/rig_v5t.blend" "$W/rig_v5c.blend" Attack Fidget Hit
FLOOR=1 run sword_clear.py "$W/rig_v5c.blend" "$W/rig_v5c.blend" Death
# the chop's crouch puts the left hand on the thigh, the death's right fist on the thigh: arm clearance (m406)
run arm_clear.py "$W/rig_v5c.blend" "$W/rig_v5c.blend" Attack:L Death:R Death:L Running:L
# the run's carry is solved per frame: its last frame (forced to the first) jumped 37 deg; spread the seam over 6 frames
FIX=1 K=6 run loop_close.py "$W/rig_v5c.blend" "$W/rig_v5c.blend" Running B_R_Clavicle B_R_UpperArm B_R_Forearm B_R_Hand
FA=0.6 run rebake_twist.py "$W/rig_v5c.blend" "$W/rig_v5.blend" Attack Fidget Hit Death Running
fi
