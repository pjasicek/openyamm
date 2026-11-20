#!/usr/bin/env bash
# m214 replayable chain (adapted from mm6_natm_claude). Prints the gate lines; aborts on the first failure.
# STAGE=rig: cleanup -> joints -> source-frame rig -> fitted fingers; STAGE=anim: retarget -> run fit -> feet -> bow carry
# -> bow/string/arrow rig -> attack/fidget/tracks -> timing -> twist -> weights -> fingers -> reduction -> left bow fist.
# Token: CREATURE_3D_TOKEN (the project lease). Run from the repository root or anywhere.
set -euo pipefail
here="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
repo="$(cd -- "$here/../../.." && pwd)"
cd "$repo"
. "$here/scripts/libpath.sh"
P=level_generation/creatures/mm7_m214_claude; W="$repo/$P/work"
run() { local out log; out=$(tools/run_creature_blender.sh --token "$CREATURE_3D_TOKEN" "$P/scripts/$1" "${@:2}" 2>&1) || {
          log=$(echo "$out" | sed -n 's/^Blender log: //p'); tail -25 "$log"; echo "STEP FAILED: $1"; exit 1; }
        log=$(echo "$out" | sed -n 's/^Blender log: //p')
        grep -E '^(BOBSMOOTH|DESPIKE|ARMHOLD|ELBOWCLEAR|CLEAN|JOINTS|SYMMETRY|RIG|HAND|WEIGHTS|THUMBCUT|KNUCKLE|FINGER|FJ|HANDFRAME|RETARGET|RUNFIT|FOOTLEVEL|CARRY|BOWRIG|ATTACK|FIDGET|TRACKS|TIMING|TWIST|GARMENT|RULE|REDUCE|HANDLE|GRIPSOLVE|GRIP )' "$log" | cut -c1-240 || true; }
STAGE=${STAGE:-all}
if [ "$STAGE" = all ] || [ "$STAGE" = rig ]; then
run step1_clean.py "$W/st_v1_parts.blend" "$W/step1.blend"
run joints_m214.py "$W/step1.blend"
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
run retarget.py "$W/rig_v1.blend" "$W/rig_v2s.blend" "$L/2Hand Bow.glb:2HandBowIdle:GripRef" "${SETC[@]}"
run retarget_mixamo.py "$W/rig_v2s.blend" "$W/rig_v2r.blend" "${MXC[@]}"
# left bow fist on the unanimated weights (the Bow bone is fitted to this handle)
SIDE=L run grip_from_source.py "$L/2Hand Bow.glb" 2HandBowIdle:0
run weights_fix.py "$W/rig_v2r.blend" "$W/rig_w.blend"
HAND_PIECES=4,5 run finger_weights.py "$W/rig_w.blend" "$W/rig_wf.blend"
SIDE=L R_HANDLE=0.014 run grip_solve.py "$W/rig_wf.blend" GripRef 0
run run_fit.py "$W/rig_v2r.blend" "$W/rig_v2f.blend"
run foot_level.py "$W/rig_v2f.blend" "$W/rig_v2l.blend" Standing Walking:const Hit Death:until=30 Draw Recoil Running:rollonly
# the walk's pelvis hitch after each heel strike (source Walk) low-passed, legs re-solved to the same feet (user
# review 2026-10-20: the head went down, up, down)
run bob_smooth.py "$W/rig_v2l.blend" "$W/rig_v2l.blend" Walking
SIDE=L run author_carry.py "$W/rig_v2l.blend" "$W/rig_v2c.blend" Standing:0.3 Running:0.2:yaw=-20:pitch=-8:x=0.37:y=-0.22 Hit:0.4:yaw=-4:x=0.35
# user review 2026-10-20: the walk tucked the carrying elbow in and put the hand in front of the thigh; the walk
# holds the idle's arm (world orientation) with a small swing against the right arm
SIDE=L run arm_hold.py "$W/rig_v2c.blend" "$W/rig_v2c.blend" Standing:1 Walking:6
BOW_ROLL=${BOW_ROLL:-15.9} run bow_rig.py "$W/rig_v2c.blend" "$W/rig_v2b.blend"
run author_bow.py "$W/rig_v2b.blend" "$W/rig_v2a.blend"
run clip_timing.py "$W/rig_v2a.blend" "$W/rig_v2.blend"
FA=0.6 FA_RAMP=0.15,0.85 run twist_bones.py "$W/rig_v2.blend" "$W/rig_v2t.blend"
run weights_fix.py "$W/rig_v2t.blend" "$W/rig_v3.blend"
HAND_PIECES=4,5 run finger_weights.py "$W/rig_v3.blend" "$W/rig_v4f.blend"
run reduce_rigged.py "$W/rig_v4f.blend" "$W/rig_v4.blend"
SIDE=L run apply_grip.py "$W/rig_v4.blend" "$W/rig_v5.blend"
# the right elbow turned out of the neck where the hand reaches the quiver (arm_torso_probe.py, frame 10), on the final
# weights; then the twist bones rebaked for the turned forearm
run elbow_clear.py "$W/rig_v5.blend" "$W/rig_v5.blend" Attack:R
FA=0.6 run rebake_twist.py "$W/rig_v5.blend" "$W/rig_v5.blend" Attack
fi
