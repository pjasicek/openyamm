#!/bin/bash
# compose -> grade -> head tiers -> alpha -> tiers -> cloth (from the project folder)
V=../claude_shared/gltf_venv/bin/python
$V -W ignore scripts/compose_banshee.py 2>&1 | tail -1 | cut -c1-160
[ -f work/white.png ] || python3 -c "from PIL import Image; Image.new('L',(64,64),255).save('work/white.png')"
$V -W ignore ../claude_shared/grade_basecolor.py --ao work/white.png --ao-strength 0 --fine 1.0 --local 0.25 --contrast 1.04 --saturation 1.05 textures/banshee_basecolor.png textures/banshee_head_a.png textures/banshee_head_c.png 2>&1 | tail -1 | cut -c1-120
$V -W ignore scripts/soften.py 2>&1 | tail -1
$V -W ignore scripts/head_b.py 2>&1 | tail -1
$V -W ignore scripts/alpha_map.py a b c 2>&1 | tail -1
$V -W ignore scripts/cloth_tex.py 2>&1 | tail -1
$V -W ignore scripts/tier_ramps.py 2>&1 | tail -1
