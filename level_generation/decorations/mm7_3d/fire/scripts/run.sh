#!/bin/bash
# Build, review and sheet one model: run.sh <build script> <variant or -> <prop> <outdoor|dungeon> <yaw> <native...>
set -e
cd "$(dirname "$0")/.."
script=$1; variant=$2; prop=$3; light=$4; yaw=$5; shift 5
if [ "$variant" = "-" ]; then
    blender --background --python "scripts/$script" 2>&1 | grep -E "LEVEL|EXPORTED|Error|Traceback|line [0-9]"
else
    blender --background --python "scripts/$script" -- "$variant" 2>&1 | grep -E "LEVEL|EXPORTED|Error|Traceback|line [0-9]"
fi
blender --background --python scripts/review.py -- "$prop" "work/${prop}_export.glb" "$light" "$yaw" 2>&1 \
    | grep -E "REVIEW|Error|Traceback"
python3 scripts/sheet.py "$prop" "$@"
