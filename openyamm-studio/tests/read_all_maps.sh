#!/usr/bin/env bash
# S0 acceptance: oymap reads every shipped MM6-MM9 map. Exports each .odm and .blv under an asset root (summary and
# full form) and fails if any cannot be read. Usage: tests/read_all_maps.sh [asset root] [oymap binary]
set -uo pipefail
here="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
root="${1:-$here/../assets_dev}"
oymap="${2:-$here/build/oymap}"
total=0
failed=0

while IFS= read -r map; do
    total=$((total + 1))
    if ! "$oymap" export "$map" --summary >/dev/null || ! "$oymap" export "$map" >/dev/null; then
        failed=$((failed + 1))
        echo "FAILED $map"
    fi
done < <(find "$root/worlds" -path '*/maps/*' \( -name '*.odm' -o -name '*.blv' \) | sort)

echo "read $((total - failed)) of $total maps"
[ "$failed" -eq 0 ] && [ "$total" -gt 0 ]
