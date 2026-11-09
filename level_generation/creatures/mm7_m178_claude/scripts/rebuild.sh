#!/usr/bin/env bash
# m178 replayable chain (rig-first on a non-human two-armed body; scripts from mm7_m418_claude / mm7_m470_claude /
# mm6_gob2_claude). Gate outputs printed; aborts on the first failure.
#   STAGE=rig : step1 (hole repair, parts) -> labels -> Meshy joints (second estimate) -> body slices -> arm rings ->
#               joints (measured; Meshy's trunk/shoulder depths unusable) -> rig (cloned frames + 8-bone tail chain,
#               bone-heat weights, rigid hands) -> piece weight rules
#   STAGE=anim: (attack lower body authored by attack_legs.py after the feet are levelled) retarget (Mixamo; KEEP_REST: the trunk, neck and head keep the mesh's rest frames and take motion
#               relative to Standing frame 0 - the world rule tilted the head 33 deg back) -> arm abduction -> tail motion -> foot levelling -> twist -> reduction
#               -> clip timing (ready pause, blends, hit cut, death travel, floor pass)
set -euo pipefail
cd "$(dirname "$0")/.."
. scripts/libpath.sh
B=/snap/bin/blender
run() { local log; log=$("$B" --background --factory-startup --threads 4 --python-exit-code 1 --python "$@" 2>&1) || { echo "$log" | tail -20; echo "STEP FAILED: $1"; exit 1; }
        echo "$log" | grep -E '^(ATTACKLEGS|WALKBOB|INPLACE|ABDUCT|CLEAN|GARMENT|SLICES|PROFILE|ARM|JOINTS|SYM|MESHY|RIG|HAND|WEIGHTS|RETARGET|TWIST|RULE|G4GAP|G4|G6|RUNFIT|FOOTLEVEL|ATTACK|STEP|FEET|LEGS|BLENDS|TIMING|DEATH|TAIL|REDUCE)|Error|rror' | cut -c1-240 || true; }
STAGE=${STAGE:-all}
if [ "$STAGE" = all ] || [ "$STAGE" = rig ]; then
run scripts/step1_clean.py -- work/st_v1_parts.blend work/step1.blend
run scripts/garments.py -- work/step1.blend work/step1.blend
run scripts/meshy_joints.py -- meshy/rig_v1/result_rigged_character_glb_url.glb work/step1.blend
run scripts/body_slices.py -- work/step1.blend
run scripts/arm_rings.py -- work/step1.blend
python3 scripts/fit_joints.py | grep -E "SYM|tail"
rm -f work/finger_joints.json
WEIGHTS=auto HAND_FROM_FOREARM=1 run scripts/build_rig.py
run scripts/weights_fix.py -- work/rig_v1.blend work/rig_v1w.blend
fi
if [ "$STAGE" = all ] || [ "$STAGE" = anim ]; then
mapfile -t MXC < <(sed -e "s|\$MX|$MX|" "${MX_LIST:-scripts/mx_clips.txt}" | grep -v '^#' | grep .)
KEEP_REST=1 run scripts/retarget_mixamo.py -- work/rig_v1w.blend work/rig_v2r.blend "${MXC[@]}"
run scripts/arm_abduct.py -- work/rig_v2r.blend work/rig_v2b.blend ${ABDUCT:-Standing:22 Walking:14 Running:18 Hit:12 Fidget:20 Attack:14:40-69}
run scripts/tail_bones.py -- work/rig_v2b.blend work/rig_v2c.blend
run scripts/foot_level.py -- work/rig_v2c.blend work/rig_v2l.blend Standing Walking:const Hit Fidget Death:until=20 Running:rollonly
run scripts/plant_feet.py -- work/rig_v2l.blend work/rig_v2p.blend Standing Fidget
# user review 2026-10-20 ("use feet"): the attack's lower body is authored on the levelled Standing feet (step, crouch, hip lead)
run scripts/attack_legs.py -- work/rig_v2p.blend work/rig_v2.blend
FA=0.6 FA_RAMP=0.15,0.85 run scripts/twist_bones.py -- work/rig_v2.blend work/rig_v2t.blend
run scripts/reduce_rigged.py -- work/rig_v2t.blend work/rig_v4.blend
HIT_END=${HIT_END:-26} ATTACK_SPEED=${ATTACK_SPEED:-1.1} run scripts/clip_timing.py -- work/rig_v4.blend work/rig_v5.blend
run scripts/walk_bob.py -- work/rig_v5.blend work/rig_v5.blend          # user review 2026-10-20: even walk bob (batch A)
ACTION=Running run scripts/walk_bob.py -- work/rig_v5.blend work/rig_v5.blend   # the same for the gallop (head d2 5.75 -> 1.8 cm)
fi
