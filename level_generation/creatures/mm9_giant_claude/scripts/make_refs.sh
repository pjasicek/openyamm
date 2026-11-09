#!/bin/bash
# MM9 renders for the Codex masters and comparisons: full figure with and without the mallet, torso, legs, head, hands, mallet. Repo root.
cd /home/pjasicek/github/OpenYAMM; P=level_generation/creatures/mm9_giant_claude; R=$P/references_hd; mkdir -p $R/renders
B="/snap/bin/blender --background --factory-startup --python-exit-code 1 --python $P/scripts/ref_renders.py --"
export LIGHT=FLAT
for t in 2 3; do l=$( [ $t = 2 ] && echo a || echo b ); g=$PWD/$P/source/true/giant${t}_true.glb
  $B $g $PWD/$R/renders fullw_$l 1024 2.9 2>&1 | grep -E "Error"
  HIDE_WEAPONS=1 $B $g $PWD/$R/renders full_$l 1024 2.9 2>&1 | grep -E "BOUNDS|Error"
  HIDE_WEAPONS=1 CENTER=0,0,0.45 $B $g $PWD/$R/renders torso_$l 800 1.3 2>&1 | grep -E "Error"
  HIDE_WEAPONS=1 CENTER=0,0,-0.7 $B $g $PWD/$R/renders legs_$l 800 1.3 2>&1 | grep -E "Error"
  HIDE_WEAPONS=1 CENTER=0,-0.05,1.08 $B $g $PWD/$R/renders head_$l 800 0.5 2>&1 | grep -E "Error"
  HIDE_WEAPONS=1 CENTER=-1.05,-0.2,0.4 $B $g $PWD/$R/renders rhand_$l 600 0.45 2>&1 | grep -E "Error"
  HIDE_WEAPONS=1 CENTER=1.05,-0.2,0.4 $B $g $PWD/$R/renders lhand_$l 600 0.45 2>&1 | grep -E "Error"
done
