#!/usr/bin/env bash
# Replayable chain for the druidess (rig-first route of mm6_bar1_claude / mm6_gob2_claude, plus the thief's cloak).
#   st_v1_parts -> step1 (cleanup, cloak label) -> arm_rings (joints) -> build_rig (frames, mesh hands, fingers)
#   -> retarget (Relax clips; Unarmed clips with the stance planted) -> twist -> weights -> finger weights -> cloak rig
#   -> reduce -> open fingers -> death arm offset -> clip timing -> cloak sim -> gates (G4/G5/G6, cloak)
# Prerequisites (one-off, kept in work/): meshy_joints.json (meshy_joints.py on the Meshy rig), source_rest.json.
set -euo pipefail
cd "$(dirname "$0")/.."
. scripts/libpath.sh
B=/snap/bin/blender
run() { local log; log=$("$B" --background --factory-startup --python-exit-code 1 --python "$@" 2>&1) || { echo "$log" | tail -20; echo "STEP FAILED: $1"; exit 1; }
        echo "$log" | grep -E '^(DROPPED|CLOAK|TRIS|ARM|ANKLE|RIG|HAND|WEIGHTS|RETARGET|PLANT|TWIST|RULE|FINGER|THUMBCUT|FINGERFIT|FJ|HANDFRAME|REDUCE|CHAIN|ARMOFFSET|STANCE|WALKDAMP|DEATHLEGS|ATTACK|CAST|HIT|CAPSULE|G4|G6|HANDSTRETCH|POKE|TEAR|SYNC|CLOAKGATE)|Error|rror' | cut -c1-220 || true; }
# FROM=cloak resumes at the cloak rig (work/rig_v4f.blend must exist)
if [ "${FROM:-}" != cloak ]; then
run scripts/step1_clean.py -- work/st_v1_parts.blend work/step1.blend
run scripts/arm_rings.py -- work/step1.blend
rm -f work/finger_joints.json
run scripts/build_rig.py
run scripts/fit_fingers.py -- work/rig_v1.blend
run scripts/finger_joints.py -- work/rig_v1.blend
run scripts/build_rig.py
run scripts/hand_frame_check.py -- work/rig_v1.blend
run scripts/retarget.py -- work/rig_v1.blend work/rig_v2a.blend "$L/Relax.glb:RelaxIdle:Standing" \
    "$L/Relax.glb:RelaxWalkFemale:Walking" "$L/Relax.glb:RelaxLaydownLayDown:Death" "$L/Relax.glb:RelaxDrink1:Fidget"
PLANT_FROM=Standing run scripts/retarget.py -- work/rig_v2a.blend work/rig_v2.blend \
    "$L/Unarmed.glb:UnarmedCastRBuff2:Attack" "$L/Unarmed.glb:UnarmedCastDualAttack2:Cast" "$L/Unarmed.glb:UnarmedGetHitF1:Hit"
run scripts/twist_bones.py -- work/rig_v2.blend work/rig_v2t.blend
run scripts/weights_fix.py -- work/rig_v2t.blend work/rig_v3.blend
run scripts/finger_weights.py -- work/rig_v3.blend work/rig_v4f.blend
fi
run scripts/cloak_rig.py -- work/rig_v4f.blend work/rig_v4c.blend
run scripts/reduce_rigged.py -- work/rig_v4c.blend work/rig_v4.blend
run scripts/fingers_relax.py -- work/rig_v4.blend work/rig_v4o.blend
# G6: at the kneel the right hand sank 5 cm into the raised left knee (our thigh is shorter than the source's)
run scripts/arm_offset.py -- work/rig_v4o.blend work/rig_v4d.blend Death R 30 6 14 24 34
# native ata c/d: the raised casting arm stands diagonally out to the side, not vertical (G4: the vertical arm stretched
# the armpit 4x)
run scripts/arm_offset.py -- work/rig_v4d.blend work/rig_v4e.blend Attack R ${ATK_TILT:--25} 9 14 22 26   # negative: outward for a RAISED arm (the sign is defined for a hanging arm)
# native dru1sta stands with the feet together; the Relax idle (and the planted clips) stand shoulder-width apart
STANCE_DEG=${STANCE_DEG:-4.5} run scripts/narrow_stance.py -- work/rig_v4e.blend work/rig_v4n.blend
# user reviews 1-2: the female walk's hips swung +-34.5 deg; pelvis oscillation x0.12, lateral sway x0.25
WALK_ROT_K=${WALK_ROT_K:-0.12} WALK_X_K=${WALK_X_K:-0.25} run scripts/walk_damp.py -- work/rig_v4n.blend work/rig_v4w.blend
# user review 1 (image 4): the prone corpse's bent legs came through the cloak; legs straightened, level, feet pointed
run scripts/death_legs.py -- work/rig_v4w.blend work/rig_v4x.blend
run scripts/clip_timing_dru.py -- work/rig_v4x.blend work/rig_v5t.blend
[ "${STOP_BEFORE_SIM:-}" ] && exit 0
CLOAK_NARROW=${CLOAK_NARROW:-0.5} run scripts/cloak_sim.py -- work/rig_v5t.blend work/rig_v5c.blend
run scripts/g4_weights.py -- work/rig_v5c.blend v5 ${G4_POSES:-Standing:0 Walking:6 Walking:18 Attack:8 Attack:15 Attack:19 Attack:23 Cast:14 Cast:22 Hit:6 Hit:10 Death:30 Death:55 Fidget:15}
run scripts/g6_contacts.py -- work/rig_v5c.blend Standing Walking Attack Cast Hit Death Fidget
run scripts/g5_hand_stretch.py -- work/rig_v5c.blend Standing:0 Walking Attack Cast Hit Death Fidget
# the textured master (export_uploads -> transfer_uv -> eye_caps: work/rig_v6.blend) takes the clips without touching its
# UVs, head split or eye caps
[ -f work/rig_v6.blend ] && run scripts/sync_actions.py -- work/rig_v5c.blend work/rig_v6.blend
run scripts/cloak_gate.py -- work/rig_v5c.blend Standing Walking Attack Cast Hit Death Fidget
