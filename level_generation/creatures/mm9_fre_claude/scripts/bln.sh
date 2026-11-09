#!/usr/bin/env bash
# Pass 7: run a Fre project Blender script through the lease wrapper under the 12G memory cap (one Blender at a time, --threads 4 set
# by the wrapper). Usage (repo root): level_generation/creatures/mm9_fre_claude/scripts/bln.sh <script.py relative to project> [args...]
set -uo pipefail
P=level_generation/creatures/mm9_fre_claude
T=$(cat $P/work/nh/lease_token.txt)
s=$1; shift
out=$(systemd-run --user --scope -q -p MemoryMax=12G -p MemorySwapMax=0 tools/run_creature_blender.sh --token "$T" "$P/$s" "$@" 2>&1); rc=$?
log=$(echo "$out" | sed -n 's/^Blender log: //p')
if [[ -n "$log" ]]; then grep -v -E "^(Read|Fra:|Saved|Time|Blender quit| *$|Info:|.*Import finished|Warning: .*Unsupported)" "$log" | tail -n ${BL_TAIL:-40}; else echo "$out" | tail -20; fi
echo "[rc=$rc log=$log]"
exit $rc
