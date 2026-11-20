#!/usr/bin/env python3
"""Before/after sheet of the projected sprite detail: per rock, native x2 sprite | front before | front after |
side before | side after (neutral light, LOD0). Usage: project_sheet.py out.png rock..."""
import glob, json, os, sys
from PIL import Image, ImageDraw
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REPO = os.path.abspath(os.path.join(HERE, '..', '..', '..', '..'))
INV = {e['name']: e for e in json.load(open(os.path.join(HERE, '..', 'inventory.json')))}
out, *rocks = sys.argv[1:]
T = 300


def sprite_path(name):
    live = os.path.join(REPO, 'assets_dev', 'engine', 'decorations_x2', name)
    return live if os.path.exists(live) else os.path.join(REPO, 'assets_legacy', 'decorations_x2_mm8_20261016', name)


def tile(path):
    im = Image.open(path).convert('RGBA'); im = im.crop(im.getbbox()); s = T * 0.92 / max(im.size)
    im = im.resize((max(1, int(im.width * s)), max(1, int(im.height * s))), Image.LANCZOS)
    c = Image.new('RGBA', (T, T), (96, 100, 110, 255)); c.alpha_composite(im, ((T - im.width) // 2, T - im.height - 4))
    return c.convert('RGB')


sheet = Image.new('RGB', (T * 5, (T + 18) * len(rocks)), (255, 255, 255)); d = ImageDraw.Draw(sheet)
for r, rock in enumerate(rocks):
    R = os.path.join(HERE, 'review', rock)
    views = sorted(glob.glob(os.path.join(R, 'lod0_y*.png')))
    items = [(sprite_path(INV[rock]['files'][0]), 'native'), (os.path.join(R, 'before_project_front.png'), 'front before'),
             (views[0], 'front after'), (os.path.join(R, 'before_project_side.png'), 'side before'),
             (views[2], 'side after')]
    for i, (p, label) in enumerate(items):
        y = r * (T + 18); sheet.paste(tile(p), (i * T, y + 18)); d.text((i * T + 4, y + 3), f'{rock} {label}', fill=(0, 0, 0))
sheet.save(out); print(out)
