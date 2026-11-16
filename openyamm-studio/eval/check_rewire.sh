#!/usr/bin/env bash
# Checks an agent's rewire of a shipped map (eval/tasks.yml): builds the overlay project, installs it into a mount
# folder and requires that the replaced handlers test and do the same as the shipped ones.
#   check_rewire.sh <project folder> <map file> <least number of replaced handlers>
set -euo pipefail
studio="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
repo="$(cd "$studio/.." && pwd)"
project="$(cd "$1" && pwd)"
work="$repo/output/studio_eval/check_$(basename "$project")"
mkdir -p "$work"
"$studio/build/oymap" build "$project" --assets "$repo/assets_dev" > /dev/null
"$studio/build/oymap" install "$project" --mount "$work/mount" --assets "$repo/assets_dev" > /dev/null
"$studio/build/oymap" flow "$2" --world mm6 --assets "$repo/assets_dev" > "$work/base.json"
"$studio/build/oymap" flow "$2" --world mm6 --assets "$repo/assets_dev" --mount "$work/mount" > "$work/overlay.json"
python3 "$studio/tests/compare_flows.py" "$work/base.json" "$work/overlay.json" "$project" "$(basename "$project")" --need "$3"
