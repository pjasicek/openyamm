#!/usr/bin/env bash
# m332 replayable chain (mm7_m302_claude's peasant route without the club; no attack, no run - speed 140 < the run
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
        grep -E '^(CLEAN|JOINTS|WRIST|SYMMETRY|RIG|HAND|WEIGHTS|THUMBCUT|THUMBWALK|KNUCKLE|FINGER|FINGERCUT|FJ|HANDFRAME|RETARGET|RUNFIT|FOOTLEVEL|SWORDCLEAR|ARMCLEAR|LOOPSEAM|CARRY|BLENDS|LEGS|FEET|STEP|TIMING|TWIST|GARMENT|RULE|REDUCE|HANDLE|GRIPSOLVE|GRIP |THUMB |WALKBOB)' "$log" | cut -c1-240 || true; }
STAGE=${STAGE:-all}
if [ "$STAGE" = all ] || [ "$STAGE" = rig ]; then
run step1_clean.py "$W/st_v1_parts.blend" "$W/step1.blend"
run joints_m332.py "$W/step1.blend"
run remove_finger.py "$W/step1.blend" "$W/step1.blend"     # six digits per hand (as m190) -> thumb + four fingers
run ponytail_fix.py "$W/step1.blend" "$W/step1.blend"      # the ponytail arced away from the back like a horn
rm -f "$W/finger_joints.json"
run build_rig.py
HAND_PIECES=2,3 run fit_fingers.py "$W/rig_v1.blend"
run finger_joints.py "$W/rig_v1.blend"
run build_rig.py
run hand_frame_check.py "$W/rig_v1.blend"
fi
if [ "$STAGE" = all ] || [ "$STAGE" = anim ]; then
mapfile -t SETC < <(sed -e "s|\$L|$L|" "$here/scripts/set_clips.txt" | grep -v '^#' | grep .)
mapfile -t MXC < <(sed -e "s|\$MX|$MX|" "$here/scripts/mx_clips.txt" | grep -v '^#' | grep .)
run retarget.py "$W/rig_v1.blend" "$W/rig_v2s.blend" "${SETC[@]}"
run retarget_mixamo.py "$W/rig_v2s.blend" "$W/rig_v2r.blend" "${MXC[@]}"
# the set's hit stands in a 45 deg fighting stance (the elf turned to profile): planted on Standing (m312 plant.py)
run plant.py "$W/rig_v2r.blend" "$W/rig_v2r.blend" Hit
run foot_level.py "$W/rig_v2r.blend" "$W/rig_v2.blend" Standing Walking:const Hit Fidget Death:until=${DEATH_UNTIL:-24}
cp "$W/rig_v2.blend" "$W/rig_v2c.blend"
FA=0.6 FA_RAMP=0.15,0.85 run twist_bones.py "$W/rig_v2c.blend" "$W/rig_v2t.blend"
run weights_fix.py "$W/rig_v2t.blend" "$W/rig_v3.blend"
SMOOTH_PASSES=${SMOOTH_PASSES:-6} HAND_PIECES=2,3 run finger_weights.py "$W/rig_v3.blend" "$W/rig_v4f.blend"
run reduce_rigged.py "$W/rig_v4f.blend" "$W/rig_v4.blend"
cp "$W/rig_v4.blend" "$W/rig_v5g.blend"
for s in $(echo "${THUMB_SIDES:-LR}" | grep -o .); do SIDE=$s K=${THUMB_K:-0.5} run thumb_relax.py "$W/rig_v5g.blend" "$W/rig_v5g.blend"; done   # G5: open thumbs (both hands)
run clip_timing.py "$W/rig_v5g.blend" "$W/rig_v5t.blend"
# walk bob (batch A, mm7_m222_claude): the retarget's floor rule left a pelvis/head zigzag; both steps alike, legs re-solved
run walk_bob.py "$W/rig_v5t.blend" "$W/rig_v5t.blend"
run arm_clear.py "$W/rig_v5t.blend" "$W/rig_v5t.blend" ${ARM_CLEAR:-Walking:L Fidget:L Fidget:R Death:R}   # G6: hands entered the thighs 3-4 cm
cp "$W/rig_v5t.blend" "$W/rig_v5c.blend"
FA=0.6 run rebake_twist.py "$W/rig_v5c.blend" "$W/rig_v5.blend" Fidget Hit Death Walking Standing
fi
