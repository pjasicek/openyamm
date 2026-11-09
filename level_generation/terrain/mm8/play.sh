#!/usr/bin/env bash
set -euo pipefail
terrain_project="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
terrain_root="$(cd -- "$terrain_project/../../.." && pwd)"
terrain_mode="${1:-enhanced}"
case "$terrain_mode" in
    enhanced) terrain_quality=x2 ;;
    original) terrain_quality=x1 ;;
    *) echo 'Usage: play.sh [enhanced|original] [map.odm] [run_game options...]' >&2; exit 2 ;;
esac
if [[ $# -gt 0 ]]; then shift; fi
terrain_map=out01.odm
if [[ $# -gt 0 && "$1" != --* ]]; then terrain_map="$1"; shift; fi
if [[ "$terrain_mode" == enhanced ]]; then
    python3 "$terrain_project/install.py" --verify-installed
fi
exec "$terrain_root/tools/run_game.sh" --isolated "mm8-terrain-$terrain_mode" \
    --world mm8 --map "$terrain_map" --assets "$terrain_root/assets_dev" \
    --set "video_quality.terrain=$terrain_quality" --seconds 0 "$@"
