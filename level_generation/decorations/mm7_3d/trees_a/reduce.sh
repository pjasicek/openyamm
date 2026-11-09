#!/usr/bin/env bash
# Texture-aware reduction of a built tree's LOD0 bark (opaque faces), after ./build.sh <id> (MM7 trees_a copy of the
# mm6_reduce_pilot route): dump -> ladder (pymeshlab; the lowest step within the surface-distance limits) -> rebuild
# LOD0 with the source's alpha cards -> swap into the built GLB (alpha primitives byte-for-byte) -> winding check.
# Output: work/reduce/mm7_deco_<id>.glb. Usage: reduce.sh <id> [step]   (step e.g. r55 overrides the ladder pick)
# MESHPY: a Python with pymeshlab (default: the session venv used for this batch).
set -euo pipefail
here="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
repo="$(cd -- "$here/../../../.." && pwd)"
blender=/snap/bin/blender
meshpy="${MESHPY:-/tmp/claude-1000/-home-pjasicek-github-OpenYAMM/53a68caf-2dc9-4fcd-9e2a-654e43d315c9/scratchpad/meshvenv/bin/python}"
id="$1"
mkdir -p "$here/work/reduce"
"$blender" --background --python "$here/scripts/reduce/deco_dump.py" -- "$id" 2>&1 | grep -E "DUMP|Error|Traceback"
"$meshpy" "$here/scripts/reduce/deco_ladder.py" "$id"
step="${2:-$(python3 -c "import json; print(json.load(open('$here/work/reduce/ladder_$id.json'))['pick'] or '')")}"
if [[ -z "$step" ]]; then
  echo "NO PASSING STEP for $id"; exit 1
fi
"$blender" --background --python "$here/scripts/reduce/deco_build.py" -- "$id:$step" 2>&1 | grep -E "BUILT|Error|Traceback"
python3 "$here/scripts/reduce/deco_swap_glb.py" "$here/work/$id/mm7_deco_$id.glb" "$here/work/reduce/${id}_lod0.glb" \
  "$here/work/reduce/mm7_deco_$id.glb"
python3 "$repo/level_generation/decorations/mm8_3d/animated/scripts/check_winding.py" "$here/work/reduce/mm7_deco_$id.glb"
"$blender" --background --python "$here/scripts/reduce/deco_compare.py" -- "$id" 2>&1 | grep -E "SHOTS|Error|Traceback"
python3 - "$here" "$id" <<'PY'
import os, sys
from PIL import Image, ImageDraw
here, sid = sys.argv[1:]
rows = [[Image.open(os.path.join(here, 'work', 'reduce', f'_{sid}_{label}_{v}.png')).convert('RGB') for v in ('front', 'q34', 'close')]
        for label in ('built', 'reduced')]
sheet = Image.new('RGB', (3 * 420, 2 * 440), (90, 92, 100)); d = ImageDraw.Draw(sheet)
for r, (row, label) in enumerate(zip(rows, ('before reduction', 'bark reduced'))):
    for c, im in enumerate(row):
        sheet.paste(im, (c * 420, r * 440 + 20))
    d.text((4, r * 440 + 4), f'{sid} {label}', fill=(255, 255, 255))
os.makedirs(os.path.join(here, 'review', sid), exist_ok=True)
sheet.save(os.path.join(here, 'review', sid, 'reduce_compare.png'))
print('COMPARE', os.path.join(here, 'review', sid, 'reduce_compare.png'))
PY
