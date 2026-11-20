#!/usr/bin/env bash
# frames.sh <glb> <out png> <clip:sec,...> [views]: clay frames of a GLB (clay_frames.py, tiles and list in the scratch dir) -> one labelled sheet
set -euo pipefail
here="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
tmp="${SCRATCH:-/tmp/claude-1000/-home-pjasicek-github-OpenYAMM/de09116c-ebb3-4810-9d9f-32f9662d74eb/scratchpad}/frames"; mkdir -p "$tmp"
base="$tmp/$(basename "$2" .png)"
"$here/B.sh" clay_frames.py "$(realpath "$1")" "$base" "$3" "${4:-front,side,q34}" | grep -E "^FRAMES" >/dev/null
mv "$base.list" "$base.png.list"
python3 "$here/sheet_frames.py" "$base.png"
mv "$base.png" "$(realpath -m "$2")"
echo "SHEET $2"
