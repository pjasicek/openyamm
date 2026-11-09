#!/bin/sh
# Pose one cage skeleton and overlay its front preview on the sprite: hang_iter.sh <pose> <sprite> <w> <h> [yaw]
cd "$(dirname "$0")"
/snap/bin/blender --background --python pose_skeleton.py -- "$1" 2>&1 | grep -E "POSED|^   |LODS|Error|Traceback"
/snap/bin/blender --background ../work/skeleton_$1.blend --python pose_preview.py -- ../review/shape/$1_front.png $3 $4 $5 2>&1 | grep -E "Error"
python3 overlay.py /home/pjasicek/github/OpenYAMM/assets_dev/engine/decorations_x2/$2 ../review/shape/$1_front.png ../review/shape/$1_overlay.png
