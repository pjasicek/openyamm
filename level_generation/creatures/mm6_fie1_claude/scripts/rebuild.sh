#!/bin/sh
# Rebuild the fire elemental from the restored frames and the animation library (run from the project directory).
set -e
B=/snap/bin/blender
M=../../../anim_library/mixamo
$B --background --factory-startup --python scripts/build_figure.py 2>&1 | grep -E "FIGURE|Error|Traceback"
$B --background work/figure.blend --python scripts/retarget.py -- work/anim.blend \
    "$M/Floating.fbx:Floating:calm" \
    "$M/Standing 2H Magic Area Attack 02.fbx:Attack:1.1:2.5:float" \
    "$M/Standing React Small From Headshot.fbx:Hit:turn:float:calm" \
    "$M/Standing React Death Backward.fbx:Death:0:0.75:turn:float" 2>&1 | grep -E "RETARGET|Error|Traceback"
python3 scripts/make_texture.py
$B --background work/anim.blend --python scripts/build_model.py 2>&1 | grep -E "EXPORTED|Error|Traceback"
if [ -f scripts/finish_glb.py ]; then python3 scripts/finish_glb.py; fi
