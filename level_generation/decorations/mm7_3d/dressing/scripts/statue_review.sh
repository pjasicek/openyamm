#!/bin/sh
# Review one statue: renders (review.py) and sheet (sheet.py). Usage: statue_review.sh <prop> <yaw> <elev> [--outdoor] -- <x2 sprites...>
set -e
cd "$(dirname "$0")/.."
prop=$1; yaw=$2; elev=$3; shift 3
flag=""
if [ "$1" = "--outdoor" ]; then flag="--outdoor"; shift; fi
[ "$1" = "--" ] && shift
blender -b "work/$prop.blend" --python scripts/review.py -- "$prop" "$yaw" "$elev" $flag 2>&1 | grep -E 'REVIEW|Error' || true
python3 scripts/statue_sheet.py "$prop" "$@"
