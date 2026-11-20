#!/usr/bin/env bash
# The druidess chain (../mm6_dru1_claude/scripts/rebuild.sh, FROM the Relax retarget work/rig_v2a.blend copied from
# there) with the Attack source replaced by the library punch (Mixamo Punching (1), planted on Standing) and its
# Attack-only arm offset dropped. Every other clip's step is unchanged. Fists kept in the punch (FINGER_K_ATTACK),
# impact = furthest forward reach of the right hand (ATTACK_RELEASE=reach).
set -euo pipefail
cd "$(dirname "$0")/.."
. scripts/libpath.sh
B=/snap/bin/blender; MX=/home/pjasicek/github/OpenYAMM/anim_library/mixamo
run() { local log; log=$("$B" --background --factory-startup --python-exit-code 1 --python "$@" 2>&1) || { echo "$log" | tail -20; echo "STEP FAILED: $1"; exit 1; }
        echo "$log" | grep -E '^(WRISTTWIST|RETARGET|PLANT|TWIST|WEIGHTS|FINGER|CHAIN|REDUCE|ARMOFFSET|STANCE|WALKDAMP|DEATHLEGS|ATTACK|CAST|HIT|CAPSULE|G4|G6|HANDSTRETCH|POKE|TEAR|SYNC|CLOAKGATE)|Error|rror' | cut -c1-220 || true; }
if [ "${FROM:-}" != cloak ]; then
PLANT_FROM=Standing run scripts/retarget.py -- work/rig_v2a.blend work/rig_v2b.blend \
    "$L/Unarmed.glb:UnarmedCastDualAttack2:Cast" "$L/Unarmed.glb:UnarmedGetHitF1:Hit"
run scripts/retarget_mixamo.py -- work/rig_v2b.blend work/rig_v2.blend "$MX/${ATTACK_FBX:-Punching (1)}.fbx:Attack:plant"
# trace gate: the punch's left guard hand pronated 118 deg against the forearm (accepted clips <= 45)
TW_MAX=${TW_MAX:-20} run scripts/wrist_twist_limit.py -- work/rig_v2.blend work/rig_v2w.blend Attack ${WRIST_SIDES:-L}
run scripts/twist_bones.py -- work/rig_v2w.blend work/rig_v2t.blend
run scripts/weights_fix.py -- work/rig_v2t.blend work/rig_v3.blend
run scripts/finger_weights.py -- work/rig_v3.blend work/rig_v4f.blend
fi
run scripts/cloak_rig.py -- work/rig_v4f.blend work/rig_v4c.blend
run scripts/reduce_rigged.py -- work/rig_v4c.blend work/rig_v4.blend
FINGER_K_ATTACK_R=${FINGER_K_ATTACK_R:-1.0} FINGER_K_ATTACK_L=${FINGER_K_ATTACK_L:-0.45} run scripts/fingers_relax.py -- work/rig_v4.blend work/rig_v4o.blend
run scripts/arm_offset.py -- work/rig_v4o.blend work/rig_v4e.blend Death R 30 6 14 24 34
STANCE_DEG=${STANCE_DEG:-4.5} run scripts/narrow_stance.py -- work/rig_v4e.blend work/rig_v4n.blend
WALK_ROT_K=${WALK_ROT_K:-0.12} WALK_X_K=${WALK_X_K:-0.25} run scripts/walk_damp.py -- work/rig_v4n.blend work/rig_v4w.blend
run scripts/death_legs.py -- work/rig_v4w.blend work/rig_v4x.blend
ATTACK_RELEASE=${ATTACK_RELEASE:-reach} run scripts/clip_timing_dru.py -- work/rig_v4x.blend work/rig_v5t.blend
[ "${STOP_BEFORE_SIM:-}" ] && exit 0
CLOAK_NARROW=${CLOAK_NARROW:-0.5} run scripts/cloak_sim.py -- work/rig_v5t.blend work/rig_v5c.blend
run scripts/g4_weights.py -- work/rig_v5c.blend v5 ${G4_POSES:-Standing:0 Attack:4 Attack:9 Attack:13 Attack:16 Attack:22 Cast:14 Hit:6 Death:30}
run scripts/g6_contacts.py -- work/rig_v5c.blend Standing Attack Cast Hit
run scripts/g5_hand_stretch.py -- work/rig_v5c.blend Standing:0 Attack Cast
run scripts/cloak_gate.py -- work/rig_v5c.blend Standing Walking Attack Cast Hit Death Fidget
