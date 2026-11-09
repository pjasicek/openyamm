#!/usr/bin/env bash
# m218 replayable chain (adapted from mm7_m214_claude / mm6_natm_claude). Prints the gate lines; aborts on the first failure.
# STAGE=rig: cleanup -> joints -> source-frame rig -> fitted fingers; STAGE=anim: retarget -> run fit -> feet -> bow carry
# -> spear rig -> attack/fidget/spear track -> timing -> twist -> weights -> fingers -> reduction -> both fists.
# Token: CREATURE_3D_TOKEN (the project lease). Run from the repository root or anywhere.
set -euo pipefail
here="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
repo="$(cd -- "$here/../../.." && pwd)"
cd "$repo"
. "$here/scripts/libpath.sh"
P=level_generation/creatures/mm7_m218_claude; W="$repo/$P/work"
run() { local out log; out=$(tools/run_creature_blender.sh --token "$CREATURE_3D_TOKEN" "$P/scripts/$1" "${@:2}" 2>&1) || {
          log=$(echo "$out" | sed -n 's/^Blender log: //p'); tail -25 "$log"; echo "STEP FAILED: $1"; exit 1; }
        log=$(echo "$out" | sed -n 's/^Blender log: //p')
        grep -E '^(BOBSMOOTH|DESPIKE|ARMHOLD|SMOOTHARM|ELBOWCLEAR|REBAKE|CLEAN|JOINTS|SYMMETRY|RIG|HAND|WEIGHTS|THUMBCUT|KNUCKLE|FINGER|FJ|HANDFRAME|RETARGET|RUNFIT|FOOTLEVEL|CARRY|SPEARRIG|SPEAR|SPEARCLEAR|ATTACK|IMPACT|FIDGET|TIMING|TWIST|GARMENT|RULE|REDUCE|HANDLE|GRIPSOLVE|GRIP )' "$log" | cut -c1-240 || true; }
STAGE=${STAGE:-all}
if [ "$STAGE" = all ] || [ "$STAGE" = rig ]; then
run step1_clean.py "$W/st_v1_parts.blend" "$W/step1.blend"
run joints_m218.py "$W/step1.blend"
rm -f "$W/finger_joints.json"
run build_rig.py
HAND_PIECES=1,2 run fit_fingers.py "$W/rig_v1.blend"
run finger_joints.py "$W/rig_v1.blend"
run build_rig.py
run hand_frame_check.py "$W/rig_v1.blend"
fi
if [ "$STAGE" = all ] || [ "$STAGE" = anim ]; then
mapfile -t SETC < <(sed -e "s|\$L|$L|" "$here/scripts/set_clips.txt" | grep -v '^#' | grep .)
mapfile -t MXC < <(sed -e "s|\$MX|$MX|" "$here/scripts/mx_clips.txt" | grep -v '^#' | grep .)
run retarget.py "$W/rig_v1.blend" "$W/rig_v2s.blend" "$L/2Hand Spear.glb:2HandSpearIdle:GripRef" "${SETC[@]}"
run retarget_mixamo.py "$W/rig_v2s.blend" "$W/rig_v2r.blend" "${MXC[@]}"
# both fists on the unanimated weights (the Spear bone is fitted to the left handle)
SIDE=L run grip_from_source.py "$L/2Hand Spear.glb" 2HandSpearIdle:0
SIDE=R run grip_from_source.py "$L/2Hand Spear.glb" 2HandSpearIdle:0
run weights_fix.py "$W/rig_v2r.blend" "$W/rig_w.blend"
HAND_PIECES=1,2 run finger_weights.py "$W/rig_w.blend" "$W/rig_wf.blend"
SIDE=L R_HANDLE=0.014 run grip_solve.py "$W/rig_wf.blend" GripRef 0
SIDE=R R_HANDLE=0.014 run grip_solve.py "$W/rig_wf.blend" GripRef 0
run run_fit.py "$W/rig_v2r.blend" "$W/rig_v2f.blend"
run foot_level.py "$W/rig_v2f.blend" "$W/rig_v2l.blend" Standing Walking:const Hit Death:until=24 Thrust Running:rollonly
# the walk's pelvis hitch after each heel strike (source Walk) low-passed, legs re-solved to the same feet (user
# review 2026-10-20: the head went down, up, down)
run bob_smooth.py "$W/rig_v2l.blend" "$W/rig_v2l.blend" Walking
SIDE=L run author_carry.py "$W/rig_v2l.blend" "$W/rig_v2c.blend" ${CARRY_CLIPS:-Standing:0.3 Running:0.2:x=0.38:y=-0.18:yaw=-15 Hit:0.4:yaw=-4:x=0.35}
# user review 2026-10-20: the walk tucked the carrying elbow in and put the hand in front of the thigh; the walk
# holds the idle's arm (world orientation) with a small swing against the right arm
SIDE=L run arm_hold.py "$W/rig_v2c.blend" "$W/rig_v2c.blend" Standing:1 Walking:6
run spear_rig.py "$W/rig_v2c.blend" "$W/rig_v2b.blend"
# user review 2026-10-20: the thrust sank the right arm into the chest; the shaft line moves down and out of it
# the 16-frame return to the idle (EASE_OUT) moved the blow to 0.93 s: the wind-up ends at IMP_OUT 23.5
LSHIFT=${LSHIFT:-0.12,-0.14,0.16} IMP_OUT=${IMP_OUT:-23.5} run author_spear.py "$W/rig_v2b.blend" "$W/rig_v2a.blend"
SIDE=L EXCL_SIDES=LR BUTT=-0.85 TIP=1.15 run spear_clear.py "$W/rig_v2a.blend" "$W/rig_v2a.blend" Attack Fidget
TRACKS_ONLY=1 run author_spear.py "$W/rig_v2a.blend" "$W/rig_v2a.blend"
run clip_timing.py "$W/rig_v2a.blend" "$W/rig_v2.blend"
FA=0.6 FA_RAMP=0.15,0.85 run twist_bones.py "$W/rig_v2.blend" "$W/rig_v2t.blend"
run weights_fix.py "$W/rig_v2t.blend" "$W/rig_v3.blend"
HAND_PIECES=1,2 run finger_weights.py "$W/rig_v3.blend" "$W/rig_v4f.blend"
run reduce_rigged.py "$W/rig_v4f.blend" "$W/rig_v4.blend"
SIDE=L run apply_grip.py "$W/rig_v4.blend" "$W/rig_v4g.blend"
SIDE=R run apply_grip.py "$W/rig_v4g.blend" "$W/rig_v5.blend"
# the right arm's return to the idle (frames 26-42) smoothed: the recovery moved the elbow unevenly (user review)
SIGMA=2.5 run smooth_arm.py "$W/rig_v5.blend" "$W/rig_v5.blend" Attack:R:26-42
# the elbows turned about the shoulder -> wrist line out of the torso on the final weights (arm_torso_probe.py), then
# the twist bones rebaked for the turned forearms
run elbow_clear.py "$W/rig_v5.blend" "$W/rig_v5.blend" Attack:LR
FA=0.6 run rebake_twist.py "$W/rig_v5.blend" "$W/rig_v5.blend" Attack
fi
