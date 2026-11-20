#!/usr/bin/env bash
# Forad replayable chain (2026-10-30 rework on the playbook rig; hvm/natm route, unarmed): aborts on the first failure.
# One-off inputs: work/step1.blend (prep_forad.py), work/joints_final.json (compose_joints_forad.py), finger joints
# from the MPFB hands (prep_forad.py), work/source_rest.json + proportions.json (humanoid set source, from hvm).
# STAGE=rig: rig + hand frame check;  STAGE=anim: Mixamo clips -> walk arms -> run fit -> feet -> twist -> weights ->
# MPFB finger weights -> loose unarmed curl -> timing -> walk bob -> extra one-shot blends (Talk, Bow, AttackMelee).
set -euo pipefail
cd "$(dirname "$0")/.."
P=$(pwd)
. scripts/libpath.sh
: "${TOKEN:?set TOKEN to the workspace lease token}"
REL="level_generation/creatures/mm9_forad_claude/v2"
run() { local s=$1; shift; local out log
        out=$(cd "$P/../../../.." && tools/run_creature_blender.sh --token "$TOKEN" "$REL/scripts/$s" "$@" 2>&1) || true
        log=$(echo "$out" | grep -o '/tmp/openyamm-creature-blender-[A-Za-z0-9]*\.log' | head -1)
        if [ -z "$log" ] || grep -q "Error: script failed\|Traceback" "$log"; then grep -A12 Traceback "$log" | tail -14; echo "STEP FAILED: $s"; exit 1; fi
        grep -E '^(CLEAN|RIG|HAND|WEIGHTS|RETARGET|TWIST|RULE|FINGERS|MPF|G4|G5|G6|GRIP|RUNFIT|FOOTLEVEL|BLENDS|LEGS|FEET|STEP|TIMING|HANDFRAME|SOLE|JERK|EXTRA|ABDUCT|BOB|IMPACT)' "$log" | cut -c1-240 || true; }
W=$P/work
STAGE=${STAGE:-all}
if [ "$STAGE" = all ] || [ "$STAGE" = rig ]; then
run build_rig.py
run hand_frame_check.py $W/rig_v1.blend
fi
if [ "$STAGE" = all ] || [ "$STAGE" = anim ]; then
mapfile -t MXC < <(sed -e "s|\$MX|$MX|" scripts/mx_clips_forad.txt | grep -v '^#' | grep .)
run retarget_mixamo.py $W/rig_v1.blend $W/rig_v2r0.blend "${MXC[@]}"
ARM_ABDUCT_DEG=${WALK_ABDUCT:-6} run abduct_arms.py $W/rig_v2r0.blend $W/rig_v2r.blend Walking
RUN_STRIDE=${RUN_STRIDE:-1.8} run run_fit.py $W/rig_v2r.blend $W/rig_v2rf.blend
run foot_level.py $W/rig_v2rf.blend $W/rig_v2.blend Standing Walking:const Hit Fidget Talk Bow AttackMelee Death:until=${DEATH_UNTIL:-12}
FA=0.6 FA_RAMP=0.15,0.85 run twist_bones.py $W/rig_v2.blend $W/rig_v2t.blend
run weights_fix.py $W/rig_v2t.blend $W/rig_v3.blend
run mp_finger_weights.py $W/rig_v3.blend $W/rig_v4.blend
UNARMED=1 LEFT_CURL=${CURL:-0.6} RIGHT_CURL=${CURL:-0.6} run apply_grip.py $W/rig_v4.blend $W/rig_v5g.blend
run clip_timing.py $W/rig_v5g.blend $W/rig_v5t.blend
run walk_bob.py $W/rig_v5t.blend $W/rig_v5b.blend
run extra_timing.py $W/rig_v5b.blend $W/rig_v5.blend
fi
