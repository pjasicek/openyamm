#!/usr/bin/env bash
# B.sh <script.py relative to this scripts dir> [args...]: run in Blender under the lease ($TOKEN), print our tagged lines or the traceback
set -uo pipefail
here="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"; repo="$(cd -- "$here/../../../.." && pwd)"
s="$1"; shift
out=$(cd "$repo" && tools/run_creature_blender.sh --token "$TOKEN" "level_generation/creatures/$(basename "$(dirname "$here")")/scripts/$s" "$@" 2>&1)
log=$(echo "$out" | grep -o '/tmp/openyamm-creature-blender-[A-Za-z0-9]*\.log' | head -1)
if grep -q "Traceback\|Error: script failed" "$log"; then grep -B2 -A14 Traceback "$log" | tail -18; echo "STEP FAILED: $s ($log)"; exit 1; fi
grep -E "^[A-Z][A-Z0-9_]+ " "$log" | grep -v "^Blender\|^Read\|^Info\|^Warning\|^WARNING\|^INFO\|^DEBUG\|^Fra:" | cut -c1-${CUT:-600}
