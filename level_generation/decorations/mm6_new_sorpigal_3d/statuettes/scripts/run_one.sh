#!/bin/sh
# Full rebuild of one statuette pedestal: prep, bake, textures, build, finish (validate), review sheet.
# Usage: run_one.sh <animal> <sprite> [--install]
cd "$(dirname "$0")"
B=/snap/bin/blender
$B --background --python statuette.py -- $1 prep 2>&1 | grep -E "PREP|Error|Trace"
$B --background --python statuette.py -- $1 bake 2>&1 | grep -E "Error|Trace"
python3 statuette.py $1 textures
$B --background --python statuette.py -- $1 build 2>&1 | grep -E "EXPORTED|Error|Trace"
python3 finish.py $1 $3 | sed 's/ materials.*bytes/ bytes/'
$B --background --python review.py -- $1 2>&1 | grep -E "Error|Trace"
python3 sheet.py $1 $2
