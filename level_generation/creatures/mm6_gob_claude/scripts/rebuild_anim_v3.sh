#!/usr/bin/env bash
# Rig repair + clips (revision 3) from the pre-refit master: hand refit, arm weight bleed fix, sword seated in the
# fist, all clips authored, forearm twist baked. Output: work/rig_v2.blend (promote to final_v1.blend to export).
set -euo pipefail
here="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
blender=/snap/bin/blender
run() { "$blender" --background "$here/work/rig_v2.blend" --python "$here/scripts/$1" -- "${@:2}" 2>&1 \
  | grep -E "APPLIED|SUBDIVIDED|SOCKET|ARM BLEED|TUCKED|SHELL|REPLACED|SWATCHES|GRIP|BLADE|AUTHORED|TWIST|Error|Traceback" || true; }
cp "$here/work/final_v1_before_hand_refit.blend" "$here/work/rig_v2.blend"
run subdivide_hands.py
run refit_hands.py apply
run tuck_shoulders.py
run fix_arm_bleed.py
run fix_palm_sockets.py
run replace_sword.py
run fit_sword_grip.py 80 35 0
for clip in walking:Walking_meshy running:Running_meshy; do
  RIGHT_CURL=80 RIGHT_THUMB=35 "$blender" --background --python "$here/scripts/retarget.py" -- \
    "$here/meshy/rig_v1/result_basic_animations_${clip%%:*}_glb_url.glb" "${clip##*:}" "$here/work/rig_v2.blend" 2>&1 \
    | grep -E "RETARGETED|Error|Traceback" || true
done
"$blender" --background "$here/work/rig_v2.blend" --python "$here/scripts/author_gob.py" 2>&1 | grep -E "AUTHORED|Error|Traceback" || true
run twist_bones.py bake
