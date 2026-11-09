#!/bin/bash
# scripts/pose_sheet.sh <glb> <out png> <clip@frame>...  : clay/texture renders front, left, back, q34 of each pose (Blender, diagnosis only)
glb=$1; out=$2; shift 2
d=$(mktemp -d -p work); list=()
for p in "$@"; do n=$(echo $p | tr '@' '_'); POSE=$p VIEWS=front,left,back,q34 CENTER=0,0.1,0.2 LIGHT=STUDIO /snap/bin/blender --background --factory-startup --disable-autoexec --threads 4 --python scripts/ref_renders.py -- $PWD/$glb $PWD/$d $n 360 2.8 2>&1 | grep -E "^Error|Traceback"; list+=($n); done
python3 - "$d" "$out" "${list[@]}" <<'PY'
import sys
from PIL import Image
d, out, names = sys.argv[1], sys.argv[2], sys.argv[3:]
W = Image.new('RGB', (360 * 4, 360 * len(names)))
for r, n in enumerate(names):
    for c, v in enumerate(['front', 'left', 'back', 'q34']):
        W.paste(Image.open(f'{d}/{n}_{v}.png').convert('RGB'), (c * 360, r * 360))
W.save(out)
PY
