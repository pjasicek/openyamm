#!/bin/bash
# Head UVs for the reshaped head (repo root). NEVER re-run once the head upload went to Meshy.
P=level_generation/creatures/mm9_peasantdm3_claude
bash $P/scripts/bl.sh "TEXPASS|HEAD|Error|Trace" $P/scripts/texpass_head_uv.py $PWD/$P/work/shape_v1.blend $PWD/$P/work/texpass_head.blend $PWD/$P/texturing/pdm3_head_upload.glb $PWD/$P/work/texpass_head_uv.json > $P/work/texpass_head_uv.out 2>&1
echo UVDONE
