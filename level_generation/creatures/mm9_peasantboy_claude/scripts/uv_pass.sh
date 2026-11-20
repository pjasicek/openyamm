#!/bin/bash
# Texture-pass UVs (body, then head). Repo root. NEVER re-run once the uploads went to Meshy.
# Head: the default SLIM merge collapsed 284 merged-chart faces to zero UV area (midline/ear slivers of the mirrored mesh);
# method=ANGLE_BASED gave 0 zero-area faces and 65.9 % use (work/uvtest/h2, adopted 2026-11-02).
P=level_generation/creatures/mm9_peasantboy_claude
bash $P/scripts/bl.sh "TEXPASS|Error|Trace" $P/scripts/texpass_uv.py $PWD/$P/work/eyes_v1.blend $PWD/$P/work/texpass_uv.blend $PWD/$P/texturing/pboy_body_upload_tp.glb $PWD/$P/work/texpass_uv.json > $P/work/texpass_uv.out 2>&1
bash $P/scripts/bl.sh "TEXPASS|HEAD|Error|Trace" $P/scripts/texpass_head_uv.py $PWD/$P/work/texpass_uv.blend $PWD/$P/work/texpass_head.blend $PWD/$P/texturing/pboy_head_upload_tp.glb $PWD/$P/work/texpass_head_uv.json method=ANGLE_BASED > $P/work/texpass_head_uv.out 2>&1
echo UVDONE
