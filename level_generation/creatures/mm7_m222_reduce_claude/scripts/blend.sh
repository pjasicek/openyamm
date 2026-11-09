#!/usr/bin/env bash
# Run one project Blender script through the lease wrapper (tools/run_creature_blender.sh, TOKEN = lease token) and
# print its log. Usage: TOKEN=<lease> scripts/blend.sh <script.py> [args...]
set -uo pipefail
repo="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/../../../.." && pwd)"
s=$1; shift
out=$("$repo/tools/run_creature_blender.sh" --token "${TOKEN:?set TOKEN}" "level_generation/creatures/mm7_m222_reduce_claude/scripts/$s" "$@" 2>&1); rc=$?
log=$(echo "$out" | grep -o '/tmp/openyamm-creature-blender-[A-Za-z0-9]*\.log' | head -1)
[ -n "$log" ] && cat "$log" || echo "$out"
exit $rc
