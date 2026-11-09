#!/usr/bin/env bash
# Background Blender in a memory-capped scope (cap.sh, CAP default 8G); prints the log lines matching $PAT.
# Usage: [PAT=..] [env] scripts/bl.sh <script.py> [-- args]
set -uo pipefail
cd "$(dirname "$0")/.."
s=$1; shift
out=$(CAP=${CAP:-8G} scripts/cap.sh /snap/bin/blender --background --factory-startup --threads 4 --python-exit-code 1 -P "scripts/$s" "$@" 2>&1); rc=$?
if [ $rc -ne 0 ] || echo "$out" | grep -q "^Traceback"; then echo "$out" | grep -A14 Traceback | tail -16; echo "STEP FAILED: $s"; exit 1; fi
echo "$out" | grep -E "${PAT:-^[A-Z][A-Z0-9_]+ }" | cut -c1-250
