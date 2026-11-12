#!/usr/bin/env bash
# Identical-camera viewer shots: new and installed, every tier, into review/shots_{new,before}/m400_<t>_<name>.png
set -euo pipefail
here="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"; repo="$(cd -- "$here/../../.." && pwd)"
cd "$repo"; P=level_generation/creatures/$(basename "$here")
SPECS=$(python3 $P/scripts/shot_specs.py "$@")
for t in a b c; do for tag in new before; do
  mkdir -p $P/review/shots_$tag
  python3 level_generation/creatures/claude_shared/texpass_viewer_shots.py shots $P $P/review/shots_$tag m400_${t}_$tag $SPECS | tail -1
  for x in $P/review/shots_$tag/m400_${t}_${tag}_*.png; do mv "$x" "${x/m400_${t}_${tag}_/m400_${t}_}"; done
done; done
