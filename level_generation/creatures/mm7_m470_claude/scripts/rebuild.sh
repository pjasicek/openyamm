#!/usr/bin/env bash
# m470 replayable chain (adapted from mm6_natm_claude / mm6_bar1_claude). Gate outputs printed; aborts on the first failure.
#   STAGE=rig : step1 (parts) -> head graft -> labels -> joints (pieces + Meshy) -> rig (cloned frames, mesh hands,
#               fitted fingers) -> piece weight rules (no weight across a gap)
#   STAGE=anim: retarget (set + Mixamo) -> run fit -> foot levelling -> twist -> finger weights -> reduction -> grip
#               -> clip timing (planted slash with IK steps, ready pause, blends, death travel, floor pass)
set -euo pipefail
cd "$(dirname "$0")/.."
. scripts/libpath.sh
B=/snap/bin/blender
run() { local log; log=$("$B" --background --factory-startup --threads 4 --python-exit-code 1 --python "$@" 2>&1) || { echo "$log" | tail -20; echo "STEP FAILED: $1"; exit 1; }
        echo "$log" | grep -E '^(ABDUCT|SWORDCLEAR|CLEAN|HEAD|GARMENT|PROFILE|JOINTS|SYM|FINGERSMOOTH|FINGERPIECES|HANDSTRETCH|SUBDIV|KNUCKLE|REDUCE|RIG|HAND|WEIGHTS|RETARGET|TWIST|RULE|G4GAP|FINGERS|G4|G5|G6|GRIPSOLVE|GRIP|RUNFIT|FOOTLEVEL|WALKBOB|BOB|ATTACK|STEP|FEET|LEGS|BLENDS|TIMING|FJ|FINGERFIT|THUMBCUT|HANDFRAME)|Error|rror' | cut -c1-240 || true; }
STAGE=${STAGE:-all}
if [ "$STAGE" = all ] || [ "$STAGE" = rig ]; then
run scripts/step1_clean.py -- work/st_v1_parts.blend work/step1.blend
run scripts/garments.py -- work/step1.blend work/step1.blend
run scripts/arm_rings.py -- work/step1.blend
python3 scripts/compose_joints.py
# m470: the claws are curled into each other (connectivity split 3 of 4 fingers): the hands stay rigid on the hand
# bones, no finger fit and no finger weights (the source finger motion is not shown)
rm -f work/finger_joints.json
HAND_FROM_FOREARM=1 run scripts/build_rig.py
run scripts/weights_fix.py -- work/rig_v1.blend work/rig_v1w.blend
fi
if [ "$STAGE" = all ] || [ "$STAGE" = anim ]; then
mapfile -t SETC < <(sed -e "s|\$L|$L|" "${SET_LIST:-scripts/set_clips.txt}" | grep -v '^#' | grep .)
mapfile -t MXC < <(sed -e "s|\$MX|$MX|" "${MX_LIST:-scripts/mx_clips.txt}" | grep -v '^#' | grep .)
run scripts/retarget.py -- work/rig_v1w.blend work/rig_v2s.blend "$L/Armed.glb:ArmedIdle:GripRef" "${SETC[@]}"
run scripts/retarget_mixamo.py -- work/rig_v2s.blend work/rig_v2r.blend "${MXC[@]}"
run scripts/arm_abduct.py -- work/rig_v2r.blend work/rig_v2b.blend Standing:16 Walking:12 Fidget:16 Hit:8
run scripts/run_fit.py -- work/rig_v2b.blend work/rig_v2f.blend
# feet flat (batch C's foot_level.py, mm7_m218_claude: sole pitch + roll weighted by sole flatness, capped, smoothed)
run scripts/foot_level.py -- work/rig_v2f.blend work/rig_v2l.blend Standing Walking:const Hit Fidget Attack AttackFull Death:until=24 Running:rollonly
cp work/rig_v2l.blend work/rig_v2.blend                 # m470: unarmed, no clearance
FA=0.6 FA_RAMP=0.15,0.85 run scripts/twist_bones.py -- work/rig_v2.blend work/rig_v2t.blend
cp work/rig_v2t.blend work/rig_v4f.blend
run scripts/reduce_rigged.py -- work/rig_v4f.blend work/rig_v4.blend
ATTACK_HOLD=0.1 ATTACK_EASE=0.45 ATTACK_SPEED=${ATTACK_SPEED:-1.4} run scripts/clip_timing.py -- work/rig_v4.blend work/rig_v5.blend
run scripts/walk_bob.py -- work/rig_v5.blend work/rig_v5.blend      # even walk bob (batch A)
fi
