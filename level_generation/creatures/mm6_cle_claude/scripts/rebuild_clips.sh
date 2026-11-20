#!/bin/sh
# Clip chain after the rigged master (work/rig_v2.blend from seat_staff.py):
# carry_staff (walk/run staff carry, ring roll) -> author_clips (Standing, Attack, Cast, Hit, Fidget) ->
# author_death (Death, Dead) -> work/rig_v3.blend; library_clips replaces Attack and Cast and makes Death and Dead from
# anim_library clips (user review 2026-10-14 (2); the authored corpse's legs are the library death's end pose);
# cloak_sim bakes the cloak -> work/rig_v4.blend; the head split of
# the head retexture upload is restored (apply_head_split.py); the cloak's physical sides are found on the rest mesh
# (cloak_sides.py -> work/cloak_sides.json, also read by prepare_textures.py) and the inner side takes the outer
# side's weights (shell_weights.py, gate shell_cross.py) after single-vertex weight spikes are repaired
# (spike_weights.py); pose_audit gate.
set -e
cd "$(dirname "$0")/.."
B="/snap/bin/blender --background --python"
$B scripts/carry_staff.py 2>&1 | grep -E "STANDING|STAFF ROLL|GRID|CARRY|Error|Traceback" || true
$B scripts/author_clips.py 2>&1 | grep -E "CLIP|Error|Traceback" || true
$B scripts/author_death.py 2>&1 | grep -E "Error|Traceback" || true
# Attack, Cast, Death and Dead from the animation library (user reviews 2026-10-14), replacing the authored ones
$B scripts/library_clips.py -- rig_v3.blend 2>&1 | grep -E "LIBCLIP|Error|Traceback" || true
cp work/rig_v3.blend work/rig_v4.blend
$B scripts/cloak_sim.py -- rig_v4.blend 2>&1 | grep -E "CLOAK|FLOOR|Error|Traceback" || true
/snap/bin/blender --background work/rig_v4.blend --python scripts/apply_head_split.py 2>&1 | grep -E "HEAD_RESTORE|Error" || true
$B scripts/cloak_sides.py -- rig_v4.blend 2>&1 | grep -E "CLOAK_SIDES|Error|Traceback" || true
$B scripts/spike_weights.py -- rig_v4.blend 2>&1 | grep -E "SPIKES|Error|Traceback" || true
$B scripts/shell_weights.py -- rig_v4.blend 2>&1 | grep -E "SHELL|Error|Traceback" || true
$B scripts/shell_cross.py -- rig_v4.blend 2>&1 | grep -E "SHELL|Error|Traceback" || true
# the tunic skirt: outside weights, lining labels (its faces are removed at export) (user review 2026-10-14 (3))
$B scripts/skirt_shell.py -- rig_v4.blend 2>&1 | grep -E "SKIRT_SHELL|Error|Traceback" || true
$B scripts/pose_audit.py -- rig_v4.blend 2>&1 | grep -E "AUDIT|Error|Traceback" || true
# new hands (user review 2026-10-14): MPFB (CC0) hands posed on the staff grip / relaxed, seated on the wrists as the
# skinned objects HandL/HandR in rig_v4.blend, their skin and AO baked into the head set's freed corner
/snap/bin/blender --background work/rig_v4.blend --python scripts/hands_measure.py -- work/hands/measure.json 2>&1 \
  | grep -E "Error|Traceback" || true
/snap/bin/blender --background --factory-startup --python scripts/hands_mpfb.py -- work/hands/measure.json 2>&1 \
  | grep -E "CURLS|HANDS|Error|Traceback" || true
$B scripts/fit_hands.py 2>&1 | grep -E "FIT_HANDS|Error|Traceback" || true
$B scripts/bake_hands.py 2>&1 | grep -E "BAKED|Error|Traceback" || true
