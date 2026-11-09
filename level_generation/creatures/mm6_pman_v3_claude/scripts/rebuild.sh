#!/usr/bin/env bash
# hvm replayable chain (natm/bar1 route, unarmed peasant). Gate outputs printed; aborts on the first failure.
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
        grep -E '^(NECKSMOOTH|NECKWEIGHTS|POSTURE|WELD|JSYM|SWORDCLEAR|CLEAN|GARMENT|RIG|HAND|WEIGHTS|RETARGET|TWIST|RULE|FINGERS|REDUCE|G4|G5|G6|GRIPSOLVE|GRIP|RUNFIT|FOOTLEVEL|ATTACK|BLENDS|LEGS|FEET|STEP|TIMING|FJ|FINGERFIT|THUMBCUT|HANDFRAME|KNUCKLE|SOLE|JERK)' "$log" | cut -c1-240 || true; }
W=$P/work
STAGE=${STAGE:-all}
if [ "$STAGE" = all ] || [ "$STAGE" = rig ]; then
run step1_clean.py $W/st_v1_parts.blend $W/step1.blend
run garments.py $W/step1.blend $W/step1.blend
ELBOW_T=${ELBOW_T:-} python3 scripts/compose_joints.py | grep ELBOW
run joints_sym.py $W/step1.blend                    # pm3: one shoulder distance and height (user: "mind the shoulders")
rm -f work/finger_joints.json
run build_rig.py
run fit_fingers.py $W/rig_v1.blend
run finger_joints.py $W/rig_v1.blend
run build_rig.py
run hand_frame_check.py $W/rig_v1.blend
fi
if [ "$STAGE" = all ] || [ "$STAGE" = anim ]; then
# hvm (unarmed peasant): Mixamo clips only, no attack, no run (speed 140 < the engine's run threshold), no prop
mapfile -t MXC < <(sed -e "s|\$MX|$MX|" "${MX_LIST:-scripts/mx_clips.txt}" | grep -v '^#' | grep .)
run retarget_mixamo.py $W/rig_v1.blend $W/rig_v2r0.blend "${MXC[@]}"
# pm3 (user review 2026-10-30, shoulders "comical"): the sources drop the clavicles 15-18 deg and push them 23 deg
# forward, lean the chest and jut the neck
run posture_fix.py $W/rig_v2r0.blend $W/rig_v2r0.blend Standing Walking Fidget
ARM_ABDUCT_DEG=${WALK_ABDUCT:-6} run abduct_arms.py $W/rig_v2r0.blend $W/rig_v2r.blend Walking   # Standard Walk swings the forearms into the tunic side
run foot_level.py $W/rig_v2r.blend $W/rig_v2.blend Standing Walking:const Hit Fidget Death:until=${DEATH_UNTIL:-12}
FA=0.6 FA_RAMP=0.15,0.85 run twist_bones.py $W/rig_v2.blend $W/rig_v2t.blend
run weights_fix.py $W/rig_v2t.blend $W/rig_v3.blend
SMOOTH_PASSES=${SMOOTH_PASSES:-6} run finger_weights.py $W/rig_v3.blend $W/rig_v4f.blend
run neck_weights.py $W/rig_v4f.blend $W/rig_v4f.blend              # pm3: even weights across the head graft
run reduce_rigged.py $W/rig_v4f.blend $W/rig_v4.blend
UNARMED=1 LEFT_CURL=${CURL:-0.6} RIGHT_CURL=${CURL:-0.6} run apply_grip.py $W/rig_v4.blend $W/rig_v5g.blend
run clip_timing.py $W/rig_v5g.blend $W/rig_v5.blend
run walk_bob.py $W/rig_v5.blend $W/rig_v5.blend          # batch A/J walk fix: even pelvis bob, legs re-solved
fi
