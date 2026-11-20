#!/usr/bin/env bash
# Rebuild one MM7 flower: atlas -> Blender clump (3 LODs) -> link + cut + validate [--install] -> review renders + sheet.
# Usage: build.sh flower01 [--install] [--grade]   (--grade: adjust the atlas grading from this review, then rebuild)
set -euo pipefail
here="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
blender=/snap/bin/blender
id="$1"; shift
install=""; grade=""
for a in "$@"; do
  case "$a" in --install) install=--install ;; --grade) grade=1 ;; esac
done
cd "$here"
# Eevee needs the GPU; when other sessions leave less than 1.5 GB free, render the review on the CPU (Cycles).
free=$(nvidia-smi --query-gpu=memory.free --format=csv,noheader,nounits 2>/dev/null | head -1 || echo 99999)
if [ "${free:-99999}" -lt 1500 ]; then export FLOWERS_CPU=1; echo "GPU memory low ($free MiB): CPU review renders"; fi
atlas=$(python3 -c "import sys; sys.path.insert(0, 'scripts'); from common import atlas_of; print(atlas_of('$id'))")
run() {
  python3 scripts/make_atlas.py "$atlas" | grep -E '^(GRADED|ATLAS)' | cut -c1-120
  "$blender" --background --python scripts/build_plant.py -- "$id" 2>&1 | grep -E '^(SPREAD|FIT|LOD|Traceback|  File|[A-Za-z]*Error)' || true
  python3 scripts/post_process.py "$id" $1 | grep -E '^(VALID|CUT|INSTALLED)|Error' || true
  "$blender" --background --python scripts/render_review.py -- "$id" 2>&1 | grep -c RENDERED >/dev/null
  python3 scripts/sheet.py "$id" $2
}
if [ -n "$grade" ]; then
  run "" --grade
fi
run "$install" ""
