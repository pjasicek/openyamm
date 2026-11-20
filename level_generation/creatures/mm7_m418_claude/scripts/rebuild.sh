#!/usr/bin/env bash
# m418 replayable chain (rig-first on a non-human body; scripts from mm7_m470_claude / mm6_gob2_claude). Gate outputs
# printed; aborts on the first failure.
#   STAGE=rig : step1 (parts) -> labels -> limb profiles -> joints (measured; Meshy's auto-rig joints unusable) -> rig
#               (cloned frames + tail chain, bone-heat weights, rigid claws) -> piece weight rules
#   STAGE=anim: retarget (Mixamo Mutant set, KEEP_REST spine) -> authored death -> arm abduction -> tail motion ->
#               foot levelling -> twist -> reduction -> clip timing (blends, attack ready pause, floor pass)
set -euo pipefail
cd "$(dirname "$0")/.."
. scripts/libpath.sh
B=/snap/bin/blender
run() { local log; log=$("$B" --background --factory-startup --threads 4 --python-exit-code 1 --python "$@" 2>&1) || { echo "$log" | tail -20; echo "STEP FAILED: $1"; exit 1; }
        echo "$log" | grep -E '^(INPLACE|ABDUCT|CLEAN|GARMENT|PROFILE|JOINTS|SYM|RIG|HAND|WEIGHTS|RETARGET|TWIST|RULE|G4GAP|G4|G6|RUNFIT|FOOTLEVEL|ATTACK|STEP|FEET|LEGS|BLENDS|TIMING|DEATH|TAIL|REDUCE)|Error|rror' | cut -c1-240 || true; }
STAGE=${STAGE:-all}
if [ "$STAGE" = all ] || [ "$STAGE" = rig ]; then
run scripts/step1_clean.py -- work/st_v1_parts.blend work/step1.blend
run scripts/garments.py -- work/step1.blend work/step1.blend
run scripts/limb_profiles.py -- work/step1.blend
python3 scripts/fit_joints.py
rm -f work/finger_joints.json
WEIGHTS=auto HAND_FROM_FOREARM=1 run scripts/build_rig.py
run scripts/weights_fix.py -- work/rig_v1.blend work/rig_v1w.blend
fi
if [ "$STAGE" = all ] || [ "$STAGE" = anim ]; then
mapfile -t MXC < <(sed -e "s|\$MX|$MX|" "${MX_LIST:-scripts/mx_clips.txt}" | grep -v '^#' | grep .)
KEEP_REST=1 run scripts/retarget_mixamo.py -- work/rig_v1w.blend work/rig_v2r.blend "${MXC[@]}"
run scripts/author_death.py -- work/rig_v2r.blend work/rig_v2d.blend
run scripts/arm_abduct.py -- work/rig_v2d.blend work/rig_v2b.blend ${ABDUCT:-Standing:8 Walking:22 Running:14 Hit:22 Fidget:22 Attack:18:34-58}
run scripts/tail_bones.py -- work/rig_v2b.blend work/rig_v2c.blend
run scripts/foot_level.py -- work/rig_v2c.blend work/rig_v2l.blend Standing Walking:const Hit Fidget
cp work/rig_v2l.blend work/rig_v2.blend
FA=0.6 FA_RAMP=0.15,0.85 run scripts/twist_bones.py -- work/rig_v2.blend work/rig_v2t.blend
run scripts/reduce_rigged.py -- work/rig_v2t.blend work/rig_v4.blend
HIT_END=26 ATTACK_FROM=28 ATTACK_HOLD=0.35 ATTACK_EASE=0.4 ATTACK_SPEED=${ATTACK_SPEED:-1.0} run scripts/clip_timing.py -- work/rig_v4.blend work/rig_v5.blend
fi
