#!/usr/bin/env bash
# m254 golem replayable chain (mm7_m414_claude's source-frame route, unarmed; clip timing from mm7_m470_claude).
# Prints the gate lines; aborts on the first failure.
# STAGE=rig : cleanup -> joints (Meshy + skin rings) -> source-frame rig -> fitted fingers
# STAGE=anim: clips (set + Mixamo) -> plant -> run fit -> feet -> twist -> weights -> fingers -> reduction -> timing
# Token: CREATURE_3D_TOKEN (the project lease).
set -euo pipefail
here="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
repo="$(cd -- "$here/../../.." && pwd)"
cd "$repo"
. "$here/scripts/libpath.sh"
P=level_generation/creatures/mm7_m254_claude; W="$repo/$P/work"
run() { local out log; out=$(tools/run_creature_blender.sh --token "$CREATURE_3D_TOKEN" "$P/scripts/$1" "${@:2}" 2>&1) || {
          log=$(echo "$out" | sed -n 's/^Blender log: //p'); tail -25 "$log"; echo "STEP FAILED: $1"; exit 1; }
        log=$(echo "$out" | sed -n 's/^Blender log: //p')
        grep -E '^(CLEAN|JOINTS|SYMMETRY|RIG|HAND|WEIGHTS|THUMBCUT|THUMBWALK|KNUCKLE|FINGER|FINGERCUT|FJ|HANDFRAME|RETARGET|PLANT|RUNFIT|FOOTLEVEL|ABDUCT|LOOPSEAM|ATTACK|BLENDS|LEGS|FEET|STEP|IMPACT|TIMING|TWIST|GARMENT|RULE|REDUCE|SMASH|FLOOR|STIFF|FACE|BOB)' "$log" | cut -c1-240 || true; }
STAGE=${STAGE:-all}
if [ "$STAGE" = all ] || [ "$STAGE" = rig ]; then
run step1_clean.py "$W/st_v1_parts.blend" "$W/step1.blend"
run meshy_joints.py "$repo/$P/meshy/rig_v1/result_rigged_character_glb_url.glb" "$W/step1.blend"
run joints_m254.py "$W/step1.blend"
rm -f "$W/finger_joints.json"
run build_rig.py
HAND_PIECES=0 run fit_fingers.py "$W/rig_v1.blend"
python3 "$here/scripts/thumb_fix.py"      # straight thumb chains reaching into the palm (G5: left web 5.7x)
run finger_joints.py "$W/rig_v1.blend"
run build_rig.py
run hand_frame_check.py "$W/rig_v1.blend"
fi
if [ "$STAGE" = all ] || [ "$STAGE" = anim ]; then
mapfile -t SETC < <(sed -e "s|\$L|$L|" "$here/scripts/set_clips.txt" | grep -v '^#' | grep .)
mapfile -t MXC < <(sed -e "s|\$MX|$MX|" "$here/scripts/mx_clips.txt" | grep -v '^#' | grep .)
run retarget.py "$W/rig_v1.blend" "$W/rig_v2s.blend" "${SETC[@]}"
run retarget_mixamo.py "$W/rig_v2s.blend" "$W/rig_v2r.blend" "${MXC[@]}"
# the set's axe chop stands in a wide guard: plant it on Standing (pelvis turn 0.35, DROP of its sink kept);
# clip_timing.py then blends LEG_KEEP of AttackFull's legs back with IK steps
PELVIS_TURN=${PELVIS_TURN:-0.35} DROP=${DROP:-0.5} run plant.py "$W/rig_v2r.blend" "$W/rig_v2p.blend" Attack
# the chop is swung from behind the right shoulder with the chest turned ~90 deg to the side: face the trunk and head
# to the front (Monk rule) so both fists come down in front, square to the target like the native smash
run face_forward.py "$W/rig_v2p.blend" "$W/rig_v2q.blend" Attack
# the axe chop's arms (crossed in front of the face, hands beside the head) replaced by the native double-fist smash:
# both arms straight up, then both fists down in front of the belly (author_smash.py, numbers in its docstring/SMASH)
run author_smash.py "$W/rig_v2q.blend" "$W/rig_v2a.blend" Attack
run run_fit.py "$W/rig_v2a.blend" "$W/rig_v2f.blend"
run foot_level.py "$W/rig_v2f.blend" "$W/rig_v2.blend" Standing Walking:const Hit Fidget FidgetFull Attack AttackFull Death:until=${DEATH_UNTIL:-24} Running:rollonly
# heavy, stiff gait: the walk's pelvis hitch after each heel strike low-passed, legs re-solved to the same feet (m414)
run bob_smooth.py "$W/rig_v2.blend" "$W/rig_v2.blend" Walking
FA=0.6 FA_RAMP=0.15,0.85 run twist_bones.py "$W/rig_v2.blend" "$W/rig_v2t.blend"
run weights_fix.py "$W/rig_v2t.blend" "$W/rig_v3.blend"
SMOOTH_PASSES=${SMOOTH_PASSES:-6} HAND_PIECES=0 run finger_weights.py "$W/rig_v3.blend" "$W/rig_v4f.blend"
run reduce_rigged.py "$W/rig_v4f.blend" "$W/rig_v4.blend"
LEAD=${LEAD:-0.1} ATTACK_SPEED=${ATTACK_SPEED:-1.0} run clip_timing.py "$W/rig_v4.blend" "$W/rig_v5t.blend"
FA=0.6 run rebake_twist.py "$W/rig_v5t.blend" "$W/rig_v5.blend" Attack Fidget Hit Death Running
fi
