#!/usr/bin/env python3
"""Contact sheet of the batch's native x2 sprites (cropped to opaque, scaled to fit), labelled with id, height and
placements. Usage: sprite_sheet.py out.png id..."""
import sys, os, json
from PIL import Image, ImageDraw


def sprite_path(name):
    """A native x2 sprite: the runtime copy, else the 2026-10-16 retirement archive (read only)."""
    live = os.path.join(REPO, 'assets_dev', 'engine', 'decorations_x2', name)
    return live if os.path.exists(live) else os.path.join(REPO, 'assets_legacy', 'decorations_x2_mm8_20261016', name)


HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REPO = os.path.abspath(os.path.join(HERE, '..', '..', '..', '..'))
INV = {e['name']: e for e in json.load(open(os.path.join(HERE, '..', 'inventory.json')))}
out, *ids = sys.argv[1:]
W, H, cols = 260, 200, 6
rows = (len(ids) + cols - 1) // cols
s = Image.new('RGB', (W * cols, (H + 20) * rows), (90, 100, 90)); d = ImageDraw.Draw(s)
for i, rid in enumerate(ids):
    e = INV[rid]
    im = Image.open(sprite_path(e['files'][0])).convert('RGBA')
    bb = im.getchannel('A').point(lambda a: 255 if a > 8 else 0).getbbox(); im = im.crop(bb)
    im.thumbnail((W - 10, H - 10), Image.LANCZOS)
    x, y = (i % cols) * W, (i // cols) * (H + 20)
    s.paste(im, (x + (W - im.width) // 2, y + 20 + H - 5 - im.height), im)
    d.text((x + 4, y + 4), f"{rid} h{e['height']} w{e['width']} n{e['outdoor']}", fill=(255, 255, 255))
s.save(out); print(out)
