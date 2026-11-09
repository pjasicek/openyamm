#!/bin/sh
# Rebuild the hanging batch: textures, models, review sheets; --install also installs the GLBs.
set -e
cd "$(dirname "$0")/scripts"
BLENDER=${BLENDER:-/snap/bin/blender}
python3 make_textures.py
review() {
    "$BLENDER" --background "../work/$1.blend" --python review.py -- "$1" $3 > /dev/null 2>&1
    python3 sheet.py "$1" "$2"
}
for prop in hngncge2 empty bonecage hngncge2_long empty_long; do
    "$BLENDER" --background --python build_cage.py -- "$prop" 2>&1 | grep -E 'LEVEL|BOUNDS|EXPORTED|Error'
done
"$BLENDER" --background --python build_chandelier.py 2>&1 | grep -E 'LEVEL|BOUNDS|EXPORTED|Error'
review hngncge2 hngncge2_p546.png
review empty empty_p546.png
review bonecage bonecage_p546.png
review hngncge2_long hngncge2_p546.png
review empty_long empty_p546.png
review chndlir0 chndlir0_p546.png "0 -22"
for prop in hngncge2 empty bonecage hngncge2_long empty_long chndlir0; do
    python3 finish.py "$prop" "$@"
done
