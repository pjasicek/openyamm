#!/bin/bash
# HOF2 variant texture-pass UVs (body, then head). Repo root. NEVER re-run once the uploads went to Meshy.
P=level_generation/creatures/mm9_peasanthof_claude; W=$PWD/$P/work/hof2
bash $P/scripts/bld.sh "TEXPASS|Error|Trace" $P/scripts/texpass_uv.py $W/eyes_tri.blend $W/texpass_uv.blend $PWD/$P/texturing/phof2_body_upload_tp.glb $W/texpass_uv.json > $W/texpass_uv.out 2>&1
bash $P/scripts/bld.sh "TEXPASS|HEAD|Error|Trace" $P/scripts/texpass_head_uv.py $W/texpass_uv.blend $W/texpass_head.blend $PWD/$P/texturing/phof2_head_upload_tp.glb $W/texpass_head_uv.json > $W/texpass_head_uv.out 2>&1
echo UVDONE
