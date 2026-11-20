#!/bin/sh
# Build one model, render its review views and sheet. Usage: review.sh <build script> <prop> <native x2 file>
set -e
cd "$(dirname "$0")/.."
/snap/bin/blender --background --python "scripts/$1" -- "$2" 2>&1 | grep -E "LEVEL|TINTS|Error|Traceback|line [0-9]" || true
/snap/bin/blender --background --python scripts/review.py -- "$2" "work/$2_export.glb" 2>&1 | grep -E "Error|Traceback" || true
python3 scripts/sheet.py "$2" "$3"
