#!/bin/sh
# Same-scale review: restored sprite frames next to EEVEE renders (unlit, blended) of work/fie1.blend.
# Usage: scripts/compare_sprite.sh <out.png> <Action> <frame,...sprite names per view: front side three back>
set -e
OUT=$1; ACTION=$2; SPRITES=$3
TMP=$OUT.render.png
/snap/bin/blender --background work/fie1.blend --python scripts/render_views.py -- $TMP --actions $ACTION \
    --views front,side,three,back --size 512 --span 2.56 --centre 1.30 --engine eevee \
    --background 0.004,0.004,0.005 --hide FireElemental_LOD 2>&1 | grep -E "Error|Traceback" || true
python3 - "$OUT" "$TMP" "$SPRITES" <<'PY'
import sys
from PIL import Image
out, render, sprites = sys.argv[1], Image.open(sys.argv[2]).convert('RGBA'), sys.argv[3].split(',')
R = '../mm6_fie1/redo_2x/aligned_2x/'
sheet = Image.new('RGBA', (512 * len(sprites), 1024), (0, 0, 0, 255))
for i, name in enumerate(sprites):
    tile = Image.new('RGBA', (512, 512), (10, 10, 13, 255))
    if name != '-':
        im = Image.open(R + name + '.png').convert('RGBA')
        im = im.crop((0, max(0, im.height - 512), 512, im.height))
        tile.alpha_composite(im, (0, 512 - im.height))
    sheet.paste(tile, (512 * i, 0))
    sheet.paste(render.crop((512 * i, 0, 512 * (i + 1), 512)), (512 * i, 512))
sheet.convert('RGB').resize((256 * len(sprites), 512)).save(out)
PY
rm -f $TMP
