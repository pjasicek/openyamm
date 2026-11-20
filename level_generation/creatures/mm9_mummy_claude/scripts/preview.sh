#!/bin/bash
# scripts/preview.sh: textured bind render of the head from uv_dump + tex_preview.json (repo root cwd = project)
G=../claude_shared/gltf_venv/bin/python; TOKEN=0e9e7aaaf86748e995603f365300a6b0
python3 scripts/assemble.py work/joined.npz work/weights.npz work/asm_uv.npz --uv work/uv_dump.npz --tex work/tex_preview.json | tail -1 && $G scripts/build_glb.py work/asm_uv.npz work/test_tex.glb 2>&1 | tail -1
cd ../../..; P=level_generation/creatures/mm9_mummy_claude
CENTER=0,-0.02,1.72 tools/run_creature_blender.sh --token $TOKEN $P/scripts/ref_renders.py $PWD/$P/work/test_tex.glb $PWD/$P/review/texA h 700 0.45 2>&1 | tail -1
python3 - <<'P2'
from PIL import Image
P='/home/pjasicek/github/OpenYAMM/level_generation/creatures/mm9_mummy_claude/review/texA/'
s=Image.new('RGB',(2800,700))
for i,n in enumerate(('q34','front','left','back')): s.paste(Image.open(P+f'h_{n}.png').convert('RGB'),(i*700,0))
s.resize((1800,450)).save(P+'hsheet.png')
P2
