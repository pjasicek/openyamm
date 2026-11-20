#!/bin/bash
# re-rig -> carry UVs -> full runtime rebuild without the Blender finish paint steps' cost. Project folder. Usage: REV=rN scripts/iter.sh [--install]
S=$PWD
W=160 scripts/step_b.sh | grep -E 'Trace|Error'
F='^CARRY|Traceback|Error|^  File' W=100 scripts/run.sh carry_uv.py $S/work/help_v1.blend $S/work/uv_v1.blend $S/work/uv_v2.blend | head -1
scripts/rebuild.sh "$@"
