#!/bin/bash
# AO on the uploads, Meshy maps -> 2K/1K, gentle grade. Usage: TOKEN=.. scripts/textures.sh (project folder)
here=$(pwd); repo=$(cd ../../..; pwd); rel=level_generation/creatures/$(basename "$here"); G=$repo/level_generation/creatures/claude_shared/gltf_venv/bin/python
B() { (cd $repo; tools/run_creature_blender.sh --token $TOKEN "$@" 2>&1 | tail -1 >/dev/null); }
B $rel/scripts/dump_faces.py $here/work/uv_v2.blend $here/work/faces.npz
for s in body:zombie:zombie_body_upload:zombie_body_retex head:zombie_head:zombie_head_upload:zombie_head_retex torso:zombie_torso_b:zombie_torso_upload:zombie_torso_b_retex; do
  IFS=: read k out up job <<< "$s"
  B $rel/scripts/texpass_bake_ao.py $here/texturing/$up.glb $here/textures/${out}_ao_2k.png 0.25 2048
  $G scripts/compose_texpass.py $out meshy/$job texturing/$up.glb textures/${out}_ao_2k.png 2>&1 | grep -E 'COMPOSE|Traceback|Error' | cut -c1-200
  $G ../claude_shared/grade_basecolor.py --ao textures/${out}_ao_2k.png --fine 1.0 --local 0.3 --ao-strength 0.5 --contrast 1.06 --saturation 1.05 textures/${out}_basecolor.png 2>&1 | tail -1 | cut -c1-140
done
$G scripts/soft_detail.py 2>&1 | tail -1
