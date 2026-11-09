#!/bin/bash
# geometry + UV master (repo root). TOKEN=<lease>
P=level_generation/creatures/mm9_banshee_claude; A=$PWD/$P
$P/scripts/geom.sh
out=$(tools/run_creature_blender.sh --token $TOKEN $P/scripts/uv_banshee.py $A/work/assembled.blend $A/work/uv_v1.blend $A/texturing/banshee_body_upload.glb $A/texturing/banshee_head_upload.glb $A/work/uv_report.json 2>&1)
log=$(echo "$out"| grep -o '/tmp/openyamm[^ ]*log'|head -1); grep -E "FACES|Error|Traceback" $log | cut -c1-300
tools/run_creature_blender.sh --token $TOKEN $P/scripts/dump_uv.py $A/work/uv_v1.blend $A/work/uv_v1.npz 2>&1 | tail -1
echo UVJOB DONE
