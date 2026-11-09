#!/bin/bash
# AO on the uploads, Meshy maps -> 2K/1K, gentle grade. Project folder.
. scripts/env.sh
for s in body head; do
  TAIL=2 scripts/run.sh texpass_bake_ao.py $P/texturing/$s.glb $P/textures/${s}_ao_2k.png 0.25 2048 2>&1 | tail -1 | cut -c1-120
  $G scripts/compose_texpass.py $s meshy/retex_$s texturing/$s.glb textures/${s}_ao_2k.png 2>&1 | grep -E 'COMPOSE|Traceback|Error' | cut -c1-200
  $G ../claude_shared/grade_basecolor.py --ao textures/${s}_ao_2k.png --fine 1.0 --local 0.3 --ao-strength 0.5 --contrast 1.04 --saturation 1.0 textures/${s}_basecolor.png 2>&1 | tail -1 | cut -c1-140
done
