#!/bin/bash
# compose -> grade -> tiers (from the project folder)
V=../claude_shared/gltf_venv/bin/python
$V -W ignore scripts/compose_lich.py 2>&1 | tail -2 | cut -c1-160
$V -W ignore ../claude_shared/grade_basecolor.py --ao textures/lich_ao_final.png --fine 1.0 --local 0.3 --ao-strength 0.5 --contrast 1.06 --saturation 1.15 textures/lich_basecolor.png 2>/dev/null
$V -W ignore ../claude_shared/grade_basecolor.py --ao textures/lich_head_ao.png --fine 1.0 --local 0.3 --ao-strength 0.5 --contrast 1.06 --saturation 1.1 textures/lich_head_basecolor.png 2>/dev/null
$V -W ignore scripts/tier_ramps.py 2>&1 | tail -1
