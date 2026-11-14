#!/bin/sh
# Finish one sword after its Meshy job (README.md, "Post-process"): resize once, AO grade, blade pass, gutter fill last,
# assemble, normal convention, Blender review renders. Usage: scripts/finish.sh <icon> <job> <tag>
set -e
cd "$(dirname "$0")/.."
S=../../../creatures/claude_shared
n=$1; job=$2; tag=$3
[ -f work/$n/maps/base_color_2k.png ] || python3 scripts/post_maps.py resize $n $job
python3 $S/grade_basecolor.py work/$n/maps/base_color_2k.png --ao work/$n/maps/ao.png --fine 1.0 --local 0.3 \
  --ao-strength 0.5 --contrast 1.06 --saturation 1.15 | tail -1
python3 scripts/blade_pass.py $n
python3 $S/gutter_fill.py work/$n/layout_measure.glb work/$n/maps/basecolor.png work/$n/maps/mr.png \
  work/$n/maps/normal.png --in-place | tail -1
blender --background --python scripts/bake_maps.py -- assemble $n "$PWD/work/$n/export_$tag.glb" 2>&1 | grep -E "ASSEMBLE|Traceback"
python3 ../../../../tools/normal_map_convention.py --threshold 0.2 work/$n/export_$tag.glb
blender --background --python scripts/render_sword.py -- work/$n/export_$tag.glb review/${tag}_$n 900 2>&1 | grep -c Saved
