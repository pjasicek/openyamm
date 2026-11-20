#!/usr/bin/env bash
# m504 replayable chain (adapted from mm7_m470_claude). Gate outputs printed; aborts on the first failure.
#   STAGE=rig : step1 (one closed shell) -> labels -> joints (Meshy) -> rig (cloned frames, hands from the forearm,
#               no fingers: the fists are rigid stone) -> weights (Meshy + shoulder fade + head free of the shoulders)
#   STAGE=anim: retarget (set + Mixamo) -> arms out -> foot levelling -> twist -> reduction -> clip timing
#               (planted smash with 20 % of its legs, blow = fastest downward fist motion, blends, floor pass)
set -euo pipefail
cd "$(dirname "$0")/.."
. scripts/libpath.sh
B=/snap/bin/blender
run() { local log; log=$("$B" --background --factory-startup --threads 4 --python-exit-code 1 --python "$@" 2>&1) || { echo "$log" | tail -20; echo "STEP FAILED: $1"; exit 1; }
        echo "$log" | grep -E '^(SOLE|FISTCLEAR|ABDUCT|CLEAN|DROP|GARMENT|JOINTS|SYM|REDUCE|RIG|HAND|WEIGHTS|RETARGET|TWIST|RULE|G4GAP|G4|G6|FOOTLEVEL|ATTACK|STEP|FEET|LEGS|BLENDS|TIMING)|Error|rror' | cut -c1-240 || true; }
STAGE=${STAGE:-all}
if [ "$STAGE" = all ] || [ "$STAGE" = rig ]; then
run scripts/drop_strays.py -- work/st_v1_parts.blend
run scripts/step1_clean.py -- work/st_v1_parts.blend work/step1.blend
run scripts/garments.py -- work/step1.blend work/step1.blend
python3 scripts/compose_joints.py
rm -f work/finger_joints.json
HAND_FROM_FOREARM=1 run scripts/build_rig.py
run scripts/weights_fix.py -- work/rig_v1.blend work/rig_v1w.blend
fi
if [ "$STAGE" = all ] || [ "$STAGE" = anim ]; then
mapfile -t SETC < <(sed -e "s|\$L|$L|" "${SET_LIST:-scripts/set_clips.txt}" | grep -v '^#' | grep .)
mapfile -t MXC < <(sed -e "s|\$MX|$MX|" "${MX_LIST:-scripts/mx_clips.txt}" | grep -v '^#' | grep .)
run scripts/retarget.py -- work/rig_v1w.blend work/rig_v2s.blend "$L/Armed.glb:ArmedIdle:GripRef" "${SETC[@]}"
run scripts/retarget_mixamo.py -- work/rig_v2s.blend work/rig_v2r.blend "${MXC[@]}"
run scripts/arm_abduct.py -- work/rig_v2r.blend work/rig_v2b.blend ${ABDUCT:-Standing:14 Walking:10 Fidget:10 Hit:6 Attack:15:0-28 Attack:35:4-26:flex Fidget:10:34-56}
run scripts/foot_level.py -- work/rig_v2b.blend work/rig_v2l.blend Standing Walking:const Hit Fidget Death:until=24
FA=0.6 FA_RAMP=0.15,0.85 run scripts/twist_bones.py -- work/rig_v2l.blend work/rig_v2t.blend
run scripts/reduce_rigged.py -- work/rig_v2t.blend work/rig_v4.blend
BLOW_DOWN=1 LEAN_KEEP_ATTACK=${LEAN_KEEP_ATTACK:-0.5} ATTACK_HOLD=${ATTACK_HOLD:-0.25} ATTACK_EASE=${ATTACK_EASE:-0.45} ATTACK_SPEED=${ATTACK_SPEED:-1.4} run scripts/clip_timing.py -- work/rig_v4.blend work/rig_v5.blend
fi
if [ "$STAGE" = all ] || [ "$STAGE" = anim ]; then
# G6: keep the stone fists apart and clear of the head (iterated sphere push, smoothed swings)
cp work/rig_v5.blend work/rig_v5c.blend
for g in 1.25 1.25 1.25 1.4 1.4; do GAP=$g run scripts/fist_clear.py -- work/rig_v5c.blend work/rig_v5c.blend Attack Fidget; done
run scripts/g6_contacts.py -- work/rig_v5c.blend Standing Walking Attack Fidget Hit
run scripts/sole_probe.py -- work/rig_v5c.blend Standing Walking Attack Fidget Hit
fi
