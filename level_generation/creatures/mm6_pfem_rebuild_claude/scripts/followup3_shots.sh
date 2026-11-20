#!/usr/bin/env bash
# Follow-up 3 shots (head posture): the compare viewer (left: v3 at HEAD, right: installed) per role, side and three-quarter.
# Usage: scripts/followup3_shots.sh <out dir> [roles...]
set -uo pipefail
here="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"; repo="$(cd -- "$here/../../.." && pwd)"
out=$1; shift; mkdir -p "$out"
roles=${*:-standing walking run fidget attack_melee hit}
base='http://127.0.0.1:8912/level_generation/creatures/audit_mm678_20261111/compare_viewer/'
for r in $roles; do for v in side three-quarter; do for t in 0.25 0.6; do
  f="$out/${r}_${v}_t${t}.png"
  W=1500 H=1000 SHOT="$f" SHOT_ONLY=1 timeout 90 node "$repo/level_generation/creatures/mm6_pfem_rebuild_claude/scripts/shot_big.mjs" "${base}?tier=0&role=$r&view=$v&t=$t#mm6_pfem" >/dev/null 2>&1 || echo "FAIL $f"
done; done; done
ls "$out" | wc -l
