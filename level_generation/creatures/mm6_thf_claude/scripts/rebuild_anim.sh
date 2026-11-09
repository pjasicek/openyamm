#!/bin/sh
# Replayable rig/animation chain (run from the project directory): Meshy rig + library clips -> rig_v1 (cloak chains,
# finger rig, fist, daggers) -> native-timed clips rig_v2 -> attack -> cloak simulation baked into every clip.
set -e
B="/snap/bin/blender --background"
M=meshy
$B --python scripts/build_rig_thf.py -- $M/anim_hit_v1/result_animation_glb_url.glb:HitSrc \
  $M/anim_death_v1/result_animation_glb_url.glb:DeathSrc | grep -E "RIGID|FLOOR|SHOULDERS|Error|Traceback"
$B --python scripts/cloak_rig.py | grep -E "CLOAK|MISSING|Error|Traceback"
$B --python scripts/finger_rig.py | grep -E "HAND|Error|Traceback"
$B --python scripts/fist_solve.py | grep -E "FIST|Error|Traceback"
$B --python scripts/seat_daggers.py | grep -E "SEAT|JOINED|Error|Traceback"
$B --python scripts/build_clips_thf.py | grep -E "CLIP|FLOOR|Error|Traceback"
if [ -f scripts/attack_thf.py ]; then $B --python scripts/attack_thf.py | grep -E "ATTACK|CLIP|Error|Traceback"; fi
$B --python scripts/cloak_sim.py -- rig_v2.blend | grep -E "CLOAK|CAPSULE|Error|Traceback"
# rig_v3: the head split of the head retexture upload restored (faces and UVs; see apply_head_split.py)
cp work/rig_v2.blend work/rig_v3.blend
$B work/rig_v3.blend --python scripts/apply_head_split.py | grep -E "HEAD_RESTORE|Error"
