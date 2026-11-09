#!/bin/bash
# frames at 24 fps
B="/snap/bin/blender --background --factory-startup --python-exit-code 1 --python scripts/ref_renders.py --"
g=$PWD/source/true/trellborg1_true.glb
while read c f; do POSE=$c@$f VIEWS=q34 CENTER=0,0,0.2 LIGHT=FLAT $B $g $PWD/work/mm9p ${c}_$f 420 3.4 2>&1 | grep -E "Error"; done <<L
aware 20
fidget2 30
Hattack1 2
Hattack1 7
Hattack1 10
Hattack1 14
Hattack2 3
Hattack2 9
Hattack2 13
Hattack2 19
Rattack1 8
Rattack1 16
Rattack1 22
Taunt 12
die1 14
die2 14
L
