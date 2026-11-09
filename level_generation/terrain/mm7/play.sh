#!/usr/bin/env bash
set -euo pipefail
terrain_stage=/tmp/openyamm-mm7-terrain-review
terrain_mode="${1:-enhanced}"
case "$terrain_mode" in
    enhanced|original) ;;
    *) echo 'Usage: play.sh [enhanced|original]' >&2; exit 2 ;;
esac
if [[ ! -f "$terrain_stage/$terrain_mode/settings.ini" ]]; then
    echo 'Prepare first: python3 level_generation/terrain/mm7/prepare_review.py' >&2
    exit 1
fi
cd -- "$terrain_stage/$terrain_mode"
exec ../openyamm --world mm7
