#!/usr/bin/env bash
# Replayable chain from the cleaned mesh to the gated rig (run from anywhere). Gate outputs are printed.
#   step1.blend + meshy rig -> build_rig (frames, mesh-measured hands, mesh-fitted fingers) -> retarget (world copy)
#   -> twist_bones -> weights_fix (accessory/torso/shoulder rules) -> finger_weights -> g4_weights
set -euo pipefail
cd "$(dirname "$0")/.."
. scripts/libpath.sh
B=/snap/bin/blender
# a failing step must stop the chain (a crash once let every later gate run on a stale file)
run() { local log; log=$("$B" --background --threads 4 --python-exit-code 1 --python "$@" 2>&1) || { echo "$log" | tail -20; echo "STEP FAILED: $1"; exit 1; }
        echo "$log" | grep -E '^(REDUCE|RIG|HAND|WEIGHTS|RETARGET|SYNC|TWIST|RULE|FINGERS|G4|G6|GRIPSOLVE|GRIP|FJ|FINGERFIT|THUMBCUT)|Error|rror' | cut -c1-220 || true; }
run scripts/step1_clean.py -- work/st_v1_parts.blend work/step1.blend
run scripts/build_rig.py
# Clips (user review 2026-10-11: the set's Armed/1Hand idle, run, attack, hit and boost are a low guard): upright
# Unarmed hit from the set; Mixamo Standard Run replaces the rejected Jogging / banned RelaxRunForward. Standing and Attack
# (a slash; "Sword And Shield Attack (2)" was a shield bash
# that read as a pommel strike) and Fidget from Mixamo (retarget_mixamo.py). GripRef (the
# armed idle) only carries the source's sword grip for grip_solve; the export drops it.
run scripts/retarget.py -- work/rig_v1.blend work/rig_v2s.blend "$L/Armed.glb:ArmedIdle:GripRef" "$L/Armed.glb:ArmedWalk:Walking" \
    "$L/Unarmed.glb:UnarmedGetHitF1:Hit" "$L/Armed.glb:ArmedDeath1:Death"
run scripts/retarget_mixamo.py -- work/rig_v2s.blend work/rig_v2.blend "$MX/Standard Idle.fbx:Standing" "$MX/Standard Run.fbx:Running" \
    "$MX/Sword And Shield Slash.fbx:Attack:plant" "$MX/Standing Taunt Battlecry.fbx:Fidget:plant" \
    "$MX/Sword And Shield Slash.fbx:AttackFull:turn" "$MX/Standing Taunt Battlecry.fbx:FidgetFull:turn"
run scripts/twist_bones.py -- work/rig_v2.blend work/rig_v2t.blend
run scripts/weights_fix.py -- work/rig_v2t.blend work/rig_v3.blend
run scripts/finger_weights.py -- work/rig_v3.blend work/rig_v4f.blend
run scripts/reduce_rigged.py -- work/rig_v4f.blend work/rig_v4.blend
run scripts/grip_solve.py -- work/rig_v4.blend GripRef 8
run scripts/apply_grip.py -- work/rig_v4.blend work/rig_v5.blend
run scripts/swap_running.py -- work/rig_v5.blend work/rig_v5.blend work/rig_v5.blend
run scripts/g4_weights.py -- work/rig_v5.blend v5 Standing:0 Walking:6 Running:6 Attack:9 Attack:13 Attack:17 Attack:21 Fidget:34
run scripts/g6_contacts.py -- work/rig_v5.blend Standing Walking Running Attack Hit Fidget Death
run scripts/sync_actions.py -- work/rig_v5.blend work/rig_v6.blend
