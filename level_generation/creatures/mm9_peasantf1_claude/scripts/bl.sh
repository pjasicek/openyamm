#!/usr/bin/env bash
# Run a project Blender script through the lease wrapper and print the log's interesting lines.
# Usage (from the repo root): level_generation/creatures/mm9_peasantf1_claude/scripts/bl.sh <script.py relative to project> [args...]
set -uo pipefail
P=level_generation/creatures/mm9_peasantf1_claude
T=$(awk '{print $2}' $P/LEASE_TOKEN.txt)
s=$1; shift
out=$(tools/run_creature_blender.sh --token "$T" "$P/$s" "$@" 2>&1); rc=$?
log=$(echo "$out" | sed -n 's/^Blender log: //p')
if [[ -n "${BL_FULL:-}" ]]; then cat "$log"; else grep -v -E "^(Read|Fra:|Saved|Time|Blender quit| *$|Info:|.*Import finished|Warning: .*Unsupported)" "$log" | tail -n ${BL_TAIL:-40}; fi
echo "[rc=$rc log=$log]"
exit $rc
