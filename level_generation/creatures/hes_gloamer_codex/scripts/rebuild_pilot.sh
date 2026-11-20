#!/usr/bin/env bash
set -euo pipefail
gloamer_token="${1:?Pass the active creature lease token}"
gloamer_project=level_generation/creatures/hes_gloamer_codex
run_step() { tools/run_creature_blender.sh --token "$gloamer_token" "$gloamer_project/scripts/$1.py" "${@:2}"; }
run_step build_rig
run_step finger_weights "$gloamer_project/work/rig_v1.blend" "$gloamer_project/work/rig_fingers.blend"
run_step fit_weights
run_step check_rig
run_step retarget_mixamo "$gloamer_project/work/rig_weighted.blend" "$gloamer_project/work/rig_pilot.blend" \
    'anim_library/mixamo/Mutant Breathing Idle.fbx:Standing' \
    'anim_library/mixamo/Mutant Punch.fbx:Attack' \
    'anim_library/mixamo/Mutant Roaring.fbx:Cast'
run_step review_pilot
