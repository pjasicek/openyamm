#!/bin/bash
# Head colour per tier from the paid head paint (project folder): sym -> hair fill -> (B: hair recolour) -> face projection -> polish.
set -euo pipefail
cd "$(dirname "$0")/.."
export WINX=${WINX:-0.062}      # A: Codex painted pale curtains at the temples; B: its auburn temple hair joins the shell (0.08)
python3 scripts/hair_fill.py textures/pf_head_a_sym.png textures/pf_head_a_base.png
python3 scripts/hair_tier_b.py textures/pf_head_a_base.png textures/pf_head_b_hair.png 0.95
python3 scripts/project_face_pf6.py a references_face/out_face_a_aligned.png textures/pf_head_a_base.png textures/pf_head_a_proj.png | tail -2
WINX=${WINX_B:-0.08} python3 scripts/project_face_pf6.py b references_face/out_face_b_aligned.png textures/pf_head_b_hair.png textures/pf_head_b_proj.png | tail -1
for t in a b; do python3 scripts/head_polish.py textures/pf_head_${t}_proj.png textures/pf_head_${t}_face.png; done
