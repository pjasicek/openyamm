#!/usr/bin/env bash
# Rebuild the short-grass clump cards (plants atlas cells 0 and 1) and plants_v4.png:
# Blender card renders -> ../process_art.py [--install] -> clump previews of plants_v3 and plants_v4 -> review sheet.
# Usage: build.sh <grass_medium_01 glTF directory> [--install]
#   The directory holds grass_medium_01_2k.gltf, grass_medium_01.bin and textures/ (see README.md).
set -euo pipefail
here="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
root="$(cd -- "$here/../../../.." && pwd)"
blender=/snap/bin/blender
source_dir="$(realpath "$1")"
shift
mkdir -p "$here/work/logs" "$here/work/preview" "$here/renders" "$here/review"
"$blender" --background --python "$here/scripts/render_cards.py" -- "$source_dir" > "$here/work/logs/render_cards.log" 2>&1
grep -E "^CARD" "$here/work/logs/render_cards.log"
python3 "$here/../process_art.py" "$@"
"$blender" --background --python "$here/scripts/preview_clump.py" -- \
  "$root/assets_dev/worlds/mm6/terrain_decorations/plants_v3.png" v3 "$here/work/preview" > "$here/work/logs/preview_v3.log" 2>&1
"$blender" --background --python "$here/scripts/preview_clump.py" -- \
  "$here/../plants_v4.png" v4 "$here/work/preview" > "$here/work/logs/preview_v4.log" 2>&1
python3 "$here/scripts/review_sheet.py" "$here/work/preview" "$here/review/clump_review.png"
