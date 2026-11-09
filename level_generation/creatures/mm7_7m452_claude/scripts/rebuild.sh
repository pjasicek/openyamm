#!/usr/bin/env bash
# 7m452 replayable chain (mm7_m302_claude's peasant route with the billhook in the right fist; peasant: no attack, no run - speed 140 < the run
# threshold). Prints the gate lines; aborts on the first failure.
# STAGE=rig: cleanup -> joints -> source-frame rig -> fitted fingers; STAGE=anim: clips -> feet -> club clearance -> twist ->
# weights -> fingers -> reduction -> grip -> timing -> club clearance. Token: CREATURE_3D_TOKEN (the project lease).
set -euo pipefail
here="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
repo="$(cd -- "$here/../../.." && pwd)"
cd "$repo"
. "$here/scripts/libpath.sh"
P=level_generation/creatures/$(basename "$here"); W="$repo/$P/work"
run() { local out log; out=$(tools/run_creature_blender.sh --token "$CREATURE_3D_TOKEN" "$P/scripts/$1" "${@:2}" 2>&1) || {
          log=$(echo "$out" | sed -n 's/^Blender log: //p'); tail -25 "$log"; echo "STEP FAILED: $1"; exit 1; }
        log=$(echo "$out" | sed -n 's/^Blender log: //p')
        grep -E '^(CLEAN|JOINTS|WRIST|SYMMETRY|RIG|HAND|WEIGHTS|THUMBCUT|THUMBWALK|KNUCKLE|FINGER|FINGERCUT|FJ|HANDFRAME|RETARGET|RUNFIT|FOOTLEVEL|SWORDCLEAR|ARMCLEAR|LOOPSEAM|CARRY|BLENDS|LEGS|FEET|STEP|TIMING|FLOOR |TWIST|GARMENT|RULE|REDUCE|HANDLE|GRIPSOLVE|GRIP |THUMB |WALKBOB)' "$log" | cut -c1-240 || true; }
STAGE=${STAGE:-all}
if [ "$STAGE" = all ] || [ "$STAGE" = rig ]; then
run step1_clean.py "$W/st_v1_parts.blend" "$W/step1.blend"
run joints_7m452.py "$W/step1.blend"
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
run foot_level.py "$W/rig_v2r.blend" "$W/rig_v2.blend" Standing Walking:const Hit Fidget Death:until=${DEATH_UNTIL:-24}
# the native carries the billhook level at the hip, blade forward (7m452w*2): authored carry in the idle, walk and
# fidget (carry.json: wrist beside the right hip, the pole 6 deg out and 10 deg down in the pelvis frame); the source
# arm swing drove the blade into the floor and through the legs
[ -f "$W/grip_pose.json" ] && SIDE=R run author_carry.py "$W/rig_v2.blend" "$W/rig_v2.blend" ${CARRY_CLIPS:-Standing:0.3 Walking:0.3 Fidget:0.3}
[ -f "$W/grip_pose.json" ] && run sword_clear.py "$W/rig_v2.blend" "$W/rig_v2c.blend" Fidget Death Hit Walking Standing || cp "$W/rig_v2.blend" "$W/rig_v2c.blend"
FA=0.6 FA_RAMP=0.15,0.85 run twist_bones.py "$W/rig_v2c.blend" "$W/rig_v2t.blend"
run weights_fix.py "$W/rig_v2t.blend" "$W/rig_v3.blend"
SMOOTH_PASSES=${SMOOTH_PASSES:-6} HAND_PIECES=4,5 run finger_weights.py "$W/rig_v3.blend" "$W/rig_v4f.blend"
run reduce_rigged.py "$W/rig_v4f.blend" "$W/rig_v4.blend"
SIDE=R run grip_from_source.py "$L/Armed.glb" ArmedIdle:8
THUMB_MAX=${THUMB_MAX:-30} GRIP_TILT=0 R_HANDLE=${R_HANDLE:-0.02} run grip_solve.py "$W/rig_v4.blend" GripRef 8
run apply_grip.py "$W/rig_v4.blend" "$W/rig_v5g.blend"
SIDE=L K=${THUMB_K:-0.5} run thumb_relax.py "$W/rig_v5g.blend" "$W/rig_v5g.blend"   # G5: open left thumb
# the retargeted idle kept its feet 1.5-1.9 cm under the floor and Standing has no floor pass (review 2026-10-20)
run floor_const.py "$W/rig_v5g.blend" "$W/rig_v5g.blend" Standing
run clip_timing.py "$W/rig_v5g.blend" "$W/rig_v5t.blend"
# walk bob (batch A, mm7_m222_claude): the retarget's floor rule left a pelvis/head zigzag; both steps alike, legs re-solved
run walk_bob.py "$W/rig_v5t.blend" "$W/rig_v5t.blend"
# hit and death keep their source arms: a small wrist cock (wrist_tilt.py) levels the billhook as in the carry
TILT=${TILT:-12}; run wrist_tilt.py "$W/rig_v5t.blend" "$W/rig_v5t.blend" Hit:$TILT Death:$TILT:15-45
run sword_clear.py "$W/rig_v5t.blend" "$W/rig_v5c.blend" Fidget Hit Walking Standing
# the backward stride drove the blade 4.8 cm into the left thigh at frame 20 (review 2026-10-20): the tunic skirt over the
# thighs (garment 6) was not in the inside test, a shaft past the thigh's centre read as outside (PARITY), the butt and grip were
# sampled too sparsely (ALLVERTS, GRIP); the death clip is now Armed Death 1 (set_clips.txt)
ALLVERTS=1 NSAMP=200 GRIP=1 PARITY=1 KEEP_GARMENTS=0,1,6 MARGIN=${DEATH_MARGIN:-0.03} FLOOR=1 run sword_clear.py "$W/rig_v5c.blend" "$W/rig_v5c.blend" Death
ARM_CLEAR=${ARM_CLEAR-Walking:L Fidget:L Death:R}; [ -n "$ARM_CLEAR" ] && run arm_clear.py "$W/rig_v5c.blend" "$W/rig_v5c.blend" $ARM_CLEAR
FA=0.6 run rebake_twist.py "$W/rig_v5c.blend" "$W/rig_v5.blend" Fidget Hit Death Walking Standing
fi
