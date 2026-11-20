#!/bin/bash
# plain Blender for read-only views while a Meshy poll holds the workspace lock. Usage scripts/blv.sh script.py args
s=$1; shift
env -u PYTHONPATH /snap/bin/blender --background --factory-startup --disable-autoexec --threads 4 --python-exit-code 1 --python scripts/$s -- "$@" 2>&1 | grep -v -E "^Blender|^Read|^Saved|^Time|Fra:|^$|^ *$" | tail -${TAIL:-12}
