#!/usr/bin/env bash
# m270 replayable chain (built MIRRORED; scripts/mirror_glb.py turns the export back) (adapted from mm6_natm_claude / mm6_bar1_claude). Gate outputs printed; aborts on the first failure.
#   STAGE=rig : step1 (parts) -> labels -> joints (Meshy arms/spine, straight hidden legs) -> rig (cloned frames,
#               mesh hands, fitted fingers) -> robe weight rules (geodesic sleeves, dress skirt, no weight across a gap)
#   STAGE=anim: retarget (set + Mixamo) -> run fit -> dagger clearance -> twist -> finger weights -> reduction -> grip
#               -> clip timing (planted slash with IK steps, ready pause, blends, death travel, floor pass)
set -euo pipefail
cd "$(dirname "$0")/.."
. scripts/libpath.sh
B=/snap/bin/blender
run() { local log; log=$("$B" --background --factory-startup --threads 4 --python-exit-code 1 --python "$@" 2>&1) || { echo "$log" | tail -20; echo "STEP FAILED: $1"; exit 1; }
        echo "$log" | grep -E '^(CARRY|STAFFATTACK|STAFFBODY|SKIRT|SWORDCLEAR|CLEAN|HEAD|GARMENT|PROFILE|JOINTS|SYM|FINGERSMOOTH|FINGERPIECES|HANDSTRETCH|SUBDIV|KNUCKLE|REDUCE|RIG|HAND|WEIGHTS|RETARGET|TWIST|RULE|G4GAP|FINGERS|G4|G5|G6|GRIPSOLVE|GRIP|RUNFIT|FOOTLEVEL|LEGSKIRT|ATTACK|STEP|FEET|LEGS|BLENDS|TIMING|FJ|FINGERFIT|THUMBCUT|HANDFRAME)|Error|rror' | cut -c1-240 || true; }
STAGE=${STAGE:-all}
if [ "$STAGE" = all ] || [ "$STAGE" = rig ]; then
run scripts/step1_clean.py -- work/st_v1_parts.blend work/step1a.blend
run scripts/graft_head.py -- work/step1a.blend work/head_v1_parts.blend work/step1.blend
run scripts/garments.py -- work/step1.blend work/step1.blend
run scripts/piece_joints.py -- work/step1.blend
rm -f work/finger_joints.json
run scripts/build_rig.py
run scripts/fit_fingers.py -- work/rig_v1.blend
run scripts/finger_joints.py -- work/rig_v1.blend
run scripts/build_rig.py
run scripts/hand_frame_check.py -- work/rig_v1.blend
run scripts/weights_fix.py -- work/rig_v1.blend work/rig_v1w.blend
fi
if [ "$STAGE" = all ] || [ "$STAGE" = anim ]; then
mapfile -t SETC < <(sed -e "s|\$L|$L|" "${SET_LIST:-scripts/set_clips.txt}" | grep -v '^#' | grep .)
mapfile -t MXC < <(sed -e "s|\$MX|$MX|" "${MX_LIST:-scripts/mx_clips.txt}" | grep -v '^#' | grep .)
run scripts/retarget.py -- work/rig_v1w.blend work/rig_v2s.blend "$L/Armed.glb:ArmedIdle:GripRef" "${SETC[@]}"
run scripts/retarget_mixamo.py -- work/rig_v2s.blend work/rig_v2r.blend "${MXC[@]}"
run scripts/run_fit.py -- work/rig_v2r.blend work/rig_v2f.blend
run scripts/foot_level.py -- work/rig_v2f.blend work/rig_v2l.blend Standing Walking:const Hit Fidget AttackBody Death:until=24
# the staff carry, the authored attack and the clearance need the solved grip (work/grip_pose.json): on the first pass
# they are skipped, then the chain runs again
if [ -f work/grip_pose.json ]; then
  run scripts/author_carry.py -- work/rig_v2l.blend work/rig_v2c.blend Standing:0.3 Walking:0.3 Running:0.35 Hit:0.4 Fidget:0.3
  run scripts/author_staff_attack.py -- work/rig_v2c.blend work/rig_v2a.blend AttackBody Attack AttackBodyFull
  run scripts/sword_clear.py -- work/rig_v2a.blend work/rig_v2.blend Death
else cp work/rig_v2l.blend work/rig_v2.blend; fi
FA=0.6 FA_RAMP=0.15,0.85 run scripts/twist_bones.py -- work/rig_v2.blend work/rig_v2t.blend
run scripts/finger_weights.py -- work/rig_v2t.blend work/rig_v4f.blend
run scripts/reduce_rigged.py -- work/rig_v4f.blend work/rig_v4.blend
R_HANDLE=0.015 run scripts/grip_solve.py -- work/rig_v4.blend GripRef 8
run scripts/apply_grip.py -- work/rig_v4.blend work/rig_v5g.blend
run scripts/skirt_bones.py -- work/rig_v5g.blend work/rig_v5s.blend
run scripts/legs_follow_skirt.py -- work/rig_v5s.blend work/rig_v5s.blend
run scripts/clip_timing.py -- work/rig_v5s.blend work/rig_v5.blend
fi
