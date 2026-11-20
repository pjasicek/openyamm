#!/usr/bin/env bash
# Close-up review: the native x2 sprite (upscaled) next to LOD0 front and three-quarter at 1100 px ->
# review/<id>/closeup.png. Usage: scripts/closeup.sh <id>
set -euo pipefail
here="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
id="$1"; w="$here/work/$id"
/snap/bin/blender --background --python "$here/scripts/render_review.py" -- "$w/export.blend" "$w/big" 1100 \
    front,three_quarter Plant 2>&1 | grep -E 'Error|Traceback' || true
python3 - "$here" "$id" <<'PY'
import sys, os
from PIL import Image
here, sid = sys.argv[1:3]
sys.path.insert(0, os.path.join(here, 'scripts')); import palm_common as pc
w = os.path.join(here, 'work', sid)
s = Image.open(os.path.join(pc.SPRITES, pc.SPECIES[sid]['sprite'])).convert('RGBA')
s = s.crop(s.getbbox())
a = Image.open(os.path.join(w, 'big_Plant_front.png')).convert('RGBA'); b = Image.open(os.path.join(w, 'big_Plant_three_quarter.png')).convert('RGBA')
a = a.crop(a.getbbox()); b = b.crop(b.getbbox())
h = 1000
fit = lambda im: im.resize((int(im.width * h / im.height), h), Image.LANCZOS)
ims = [fit(s), fit(a), fit(b)]
out = Image.new('RGBA', (sum(i.width for i in ims) + 40, h + 20), (128, 138, 155, 255)); x = 10
for i in ims:
    out.alpha_composite(i, (x, 10)); x += i.width + 10
out.convert('RGB').save(os.path.join(pc.review(sid), 'closeup.png'))
print('CLOSEUP', os.path.join(pc.review(sid), 'closeup.png'))
PY
