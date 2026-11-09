#!/bin/sh
# Build, finish (validate; install with --install) and review one model of this batch.
# Usage: run.sh <build script> <prop> <native texture> [--install] [z0:z1 ...]
set -e
HERE=$(cd "$(dirname "$0")" && pwd)
BUILD=$1; PROP=$2; NATIVE=$3; shift 3
INSTALL=
if [ "$1" = "--install" ]; then INSTALL=--install; shift; fi
/snap/bin/blender --background --python "$HERE/$BUILD" -- "$PROP" 2>&1 | grep -E "^LEVEL|EXPORTED|Error|error|Traceback" || true
python3 "$HERE/finish.py" "$PROP" $INSTALL
/snap/bin/blender --background --python "$HERE/review.py" -- "$PROP" "$HERE/../work/${PROP}_export.glb" 2>&1 \
    | grep -E "^REVIEW|Error|Traceback" || true
python3 "$HERE/sheet.py" "$PROP" "$NATIVE" "$@"
