#!/usr/bin/env bash
# m438 replayable chain (mm7_m190_claude's one-handed prop route, prop in the LEFT fist as mm7_m214_claude; the right
# arm is a stump). Prints the gate lines; aborts on the first failure. Token: CREATURE_3D_TOKEN (the project lease).
# STAGE=rig: cleanup (hole fill, shin) -> joints -> source-frame rig -> fitted left fingers -> weights (labels);
# STAGE=anim: clips -> run fit -> feet -> prop clearance -> twist -> weights -> fingers -> reduction -> grip -> timing ->
# prop clearance -> arm clearance -> twist rebake. Run twice on a fresh project (the clearance needs the solved grip).
set -euo pipefail
here="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
repo="$(cd -- "$here/../../.." && pwd)"
cd "$repo"
. "$here/scripts/libpath.sh"
P=level_generation/creatures/$(basename "$here"); W="$repo/$P/work"
run() { local out log; out=$(tools/run_creature_blender.sh --token "$CREATURE_3D_TOKEN" "$P/scripts/$1" "${@:2}" 2>&1) || {
          log=$(echo "$out" | sed -n 's/^Blender log: //p'); tail -25 "$log"; echo "STEP FAILED: $1"; exit 1; }
        log=$(echo "$out" | sed -n 's/^Blender log: //p')
        grep -E '^(CLEAN|JOINTS|STUMP|WRIST|SYMMETRY|RIG|HAND|WEIGHTS|THUMBCUT|THUMBWALK|KNUCKLE|FINGER|FINGERCUT|FINGERDIR|FJ|HANDFRAME|RETARGET|RUNFIT|FOOTLEVEL|SWORDCLEAR|ARMCLEAR|LOOPSEAM|CARRY|BLENDS|LEGS|FEET|STEP|TIMING|ATTACK|TWIST|ARMHOLD|GARMENT|RULE|REDUCE|HANDLE|GRIPSOLVE|GRIP |THUMB |PROP)' "$log" | cut -c1-240 || true; }
export PROP_SIDE=L
STAGE=${STAGE:-all}
if [ "$STAGE" = all ] || [ "$STAGE" = rig ]; then
run step1_clean.py "$W/st_v1_parts.blend" "$W/step1.blend"
run joints_m438.py "$W/step1.blend"
rm -f "$W/finger_joints.json"
run build_rig.py
SIDES=L HAND_PIECES=0 run fit_fingers.py "$W/rig_v1.blend"
SIDES=L run finger_joints.py "$W/rig_v1.blend"
run build_rig.py
SIDES=L run hand_frame_check.py "$W/rig_v1.blend"
run weights_fix.py "$W/rig_v1.blend" "$W/rig_v1w.blend"          # labels (work/garments.json) for the clearance pass
# the prop from the rest skin (the texture chain rebuilds it from the textured master rig_v6 with its UVs: keep that one)
[ -f "$W/rig_v6.blend" ] || run make_forearm.py "$W/rig_v1.blend"
fi
if [ "$STAGE" = all ] || [ "$STAGE" = anim ]; then
mapfile -t SETC < <(sed -e "s|\$L|$L|" "$here/scripts/set_clips.txt" | grep -v '^#' | grep .)
mapfile -t MXC < <(sed -e "s|\$MX|$MX|" "$here/scripts/mx_clips.txt" | grep -v '^#' | grep .)
run retarget.py "$W/rig_v1.blend" "$W/rig_v2s.blend" "$L/2Hand Bow.glb:2HandBowIdle:GripRef" "${SETC[@]}"
run retarget_mixamo.py "$W/rig_v2s.blend" "$W/rig_v2r.blend" "${MXC[@]}"
run run_fit.py "$W/rig_v2r.blend" "$W/rig_v2f.blend"
run foot_level.py "$W/rig_v2f.blend" "$W/rig_v2.blend" Standing Walking:const Hit Fidget FidgetFull Attack AttackFull Death:until=${DEATH_UNTIL:-24} Running:rollonly
# the source arms swing the prop across the chest (walk, run) or turn it across the groin (idle); the native holds it
# forward at the hip: authored carry (carry_L.json) with a share of the clip's own wrist motion
[ -f "$W/grip_pose_L.json" ] && SIDE=L run author_carry.py "$W/rig_v2.blend" "$W/rig_v2.blend" ${CARRY_CLIPS:-Standing:0.3 Running:0.25:x=0.33:pitch=35}
# the drunk walk lifts and wings the carrying arm (the carry kept its abducted upper arm: elbow out ~60 deg); the walk
# holds the idle's carry arm (world orientation) with a swing against the stump arm, as mm7_m214_claude
[ -f "$W/grip_pose_L.json" ] && SIDE=L run arm_hold.py "$W/rig_v2.blend" "$W/rig_v2.blend" Standing:0 Walking:${WALK_SWING:-14}
[ -f "$W/grip_pose_L.json" ] && run prop_clear.py "$W/rig_v2.blend" "$W/rig_v2c.blend" Fidget FidgetFull Death Running Hit Attack AttackFull Walking Standing || cp "$W/rig_v2.blend" "$W/rig_v2c.blend"
FA=0.6 FA_RAMP=0.15,0.85 run twist_bones.py "$W/rig_v2c.blend" "$W/rig_v2t.blend"
run weights_fix.py "$W/rig_v2t.blend" "$W/rig_v3.blend"
SIDES=L SMOOTH_PASSES=${SMOOTH_PASSES:-6} HAND_PIECES=0 run finger_weights.py "$W/rig_v3.blend" "$W/rig_v4f.blend"
run reduce_rigged.py "$W/rig_v4f.blend" "$W/rig_v4.blend"
SIDE=L run grip_from_source.py "$L/2Hand Bow.glb" 2HandBowIdle:0
SIDE=L THUMB_MAX=${THUMB_MAX:-30} GRIP_TILT=0 R_HANDLE=${R_HANDLE:-0.030} run grip_solve.py "$W/rig_v4.blend" GripRef 0
SIDE=L run apply_grip.py "$W/rig_v4.blend" "$W/rig_v5g.blend"
LEAD=${LEAD:-0.3} run clip_timing.py "$W/rig_v5g.blend" "$W/rig_v5t.blend"
run prop_clear.py "$W/rig_v5t.blend" "$W/rig_v5c.blend" Attack Fidget Hit
FLOOR=1 run prop_clear.py "$W/rig_v5c.blend" "$W/rig_v5c.blend" Death
# the stump grazes the right thigh in the chop's recovery, the carrying hand the left thigh in the run (G6): arm clearance (m406)
run arm_clear.py "$W/rig_v5c.blend" "$W/rig_v5c.blend" ${ARM_CLEAR:-Attack:R Running:L}
FA=0.6 run rebake_twist.py "$W/rig_v5c.blend" "$W/rig_v5.blend" Attack Fidget Hit Death Running Walking Standing
fi
