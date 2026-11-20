#!/bin/bash
# MM9 renders for the Codex masters: five views of the whole figure without the club, waist, head, hand, foot. Repo root.
cd /home/pjasicek/github/OpenYAMM; P=level_generation/creatures/mm9_trellborg_claude; R=$P/references_hd; mkdir -p $R/renders
B="/snap/bin/blender --background --factory-startup --python-exit-code 1 --python $P/scripts/ref_renders.py --"
export LIGHT=FLAT
for t in 1 2 3; do l=$(echo abc | cut -c$t); g=$PWD/$P/source/true/trellborg${t}_true.glb
  HIDE_WEAPONS=1 $B $g $PWD/$R/renders full_$l 1024 2.5 2>&1 | grep -E "BOUNDS|Error"
  HIDE_WEAPONS=1 CENTER=0,0,0.18 $B $g $PWD/$R/renders torso_$l 800 1.3 2>&1 | grep -E "Error"
  HIDE_WEAPONS=1 CENTER=0,0,-0.65 $B $g $PWD/$R/renders legs_$l 800 1.2 2>&1 | grep -E "Error"
  HIDE_WEAPONS=1 CENTER=0,0,0.93 $B $g $PWD/$R/renders head_$l 800 0.62 2>&1 | grep -E "Error"
done
$B $PWD/$P/source/true/trellborg1_true.glb $PWD/$R/renders club_a 1024 2.0 2>&1 | grep -E "Error"
