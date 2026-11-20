#!/usr/bin/env bash
# Texture chain after the paid paints (project folder). Reads the graded body images; writes every *_final.png.
set -euo pipefail
PY=/home/pjasicek/github/OpenYAMM/level_generation/creatures/claude_shared/gltf_venv/bin/python
python3 scripts/project_heads.py | tail -2
$PY ../claude_shared/grade_basecolor.py --ao textures/guard_head_ao.png --fine 1.0 --local 0.15 --ao-strength 0.25 --contrast 1.04 --saturation 1.05 textures/guard_heada_basecolor.png textures/guard_headc_basecolor.png 2>&1 | grep -v Runtime | tail -1
for f in guard_heada guard_headc; do cp textures/${f}_basecolor_graded.png textures/${f}_final.png; done
python3 scripts/compose_tier_b.py | tail -2
