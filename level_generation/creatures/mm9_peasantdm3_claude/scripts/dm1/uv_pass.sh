#!/bin/bash
# Texture-pass UVs (body, then head). Repo root. NEVER re-run once the uploads went to Meshy.
P=level_generation/creatures/mm9_peasantdm1_claude
bash $P/scripts/bl.sh "TEXPASS|Error|Trace" $P/scripts/texpass_uv.py $PWD/$P/work/head_v1.blend $PWD/$P/work/texpass_uv.blend $PWD/$P/texturing/pdm1_body_upload_tp.glb $PWD/$P/work/texpass_uv.json > $P/work/texpass_uv.out 2>&1
bash $P/scripts/bl.sh "TEXPASS|HEAD|Error|Trace" $P/scripts/texpass_head_uv.py $PWD/$P/work/texpass_uv.blend $PWD/$P/work/texpass_head.blend $PWD/$P/texturing/pdm1_head_upload_tp.glb $PWD/$P/work/texpass_head_uv.json > $P/work/texpass_head_uv.out 2>&1
echo UVDONE
