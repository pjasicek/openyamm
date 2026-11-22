#!/usr/bin/env bash
# Run one Blender step of this project under the lease through the lane's Blender wrapper (one Blender at a time in
# lane S) and print its own log's result lines. Logs stay in the project (logs/), never /tmp.
# Usage: TOK=<lease> scripts/step.sh <script.py> [args...]
set -uo pipefail
here="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"; repo="$(cd -- "$here/../../.." && pwd)"
export PATH="$repo/level_generation/creatures/xeen_tiers_claude/bin:$PATH"
mkdir -p "$here/logs"
log="$here/logs/$(date +%H%M%S)_${1%.py}.log"
script="$here/scripts/$1"; [ -f "$script" ] || script="$1"
args=(); [ $# -gt 1 ] && args=(-- "${@:2}")
(cd "$repo" && python3 tools/creature_workspace.py run --project "$here" --token "$TOK" -- \
  blender --background --factory-startup --disable-autoexec --threads 4 --python-exit-code 1 \
  --python "$script" "${args[@]}" > "$log" 2>&1)
rc=$?
grep -E '^[A-Z][A-Z0-9_]+[ :]' "$log" | grep -v -E '^(Blender|FBX|Read|Info|INFO|Warning|WARNING)' | cut -c1-400
if [ $rc -ne 0 ] || grep -q "Traceback\|script failed" "$log"; then grep -A14 Traceback "$log" | head -24; echo "STEP FAILED: $1 ($log)"; exit 1; fi
