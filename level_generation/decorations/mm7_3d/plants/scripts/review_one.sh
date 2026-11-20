#!/usr/bin/env bash
# Review renders + sheet for one built model. Usage: review_one.sh <id>
set -euo pipefail
here="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
id="$1"
tris=$(grep -E '^LOD' "$here/work/logs/$id.log" | awk '{print $4}' | tr '\n' ' ')
# Eevee may crash when the GPU is short of memory: retry, then fall back to Cycles on the CPU (review.py --cpu)
for attempt in 1 2 3; do
  if [[ $attempt -lt 3 ]]; then cpu=(); else cpu=(--cpu); fi
  /snap/bin/blender --background --python "$here/scripts/review.py" -- "$id" 480 "${cpu[@]}" \
    > "$here/work/logs/${id}_review.log" 2>&1 && grep -q '^REVIEW' "$here/work/logs/${id}_review.log" && break
done
python3 "$here/scripts/sheet.py" "$id" $tris
