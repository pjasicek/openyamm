#!/usr/bin/env python3
"""Paint the scimitar swatches (from replace_sword.py) into the goblin texture sets, after compose_gob.py.
Steel strip: spine -> edge gradient with a darker fuller line; gold, leather and jewel swatches are solid.
Args: swatches_json (the scene's gob_sword_swatches string, saved by build to work/sword_swatches.json)."""
import json, sys
from pathlib import Path
import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
T = ROOT / 'textures'
sw = json.load(open(sys.argv[1] if len(sys.argv) > 1 else ROOT / 'work/sword_swatches.json'))
STEEL_SPINE, STEEL_EDGE = np.array([0.50, 0.51, 0.54]), np.array([0.86, 0.87, 0.89])
FILL = {'gold': ((0.86, 0.64, 0.26), 0.75, 0.36), 'leather': ((0.30, 0.16, 0.08), 0.0, 0.70),
        'jewel': ((0.62, 0.03, 0.05), 0.0, 0.15)}


def rect(img, r, pad=2):
    h, w = img.shape[:2]
    x0 = int(r[0] * w) - pad; x1 = int(round(r[2] * w)) + pad
    y0 = int((1 - r[3]) * h) - pad; y1 = int(round((1 - r[1]) * h)) + pad
    return max(y0, 0), min(y1, h), max(x0, 0), min(x1, w)


def paint(name, fn):
    path = T / name
    img = np.asarray(Image.open(path).convert('RGB'), dtype=np.float32) / 255.0
    fn(img)
    Image.fromarray(np.clip(img * 255 + 0.5, 0, 255).astype(np.uint8)).save(path, optimize=True)


def base(img):
    y0, y1, x0, x1 = rect(img, sw['steel'])
    u = np.clip((np.arange(x0, x1) - x0) / max(x1 - x0 - 1, 1), 0, 1)
    col = STEEL_SPINE[None] * (1 - u[:, None]) + STEEL_EDGE[None] * u[:, None]
    fuller = np.exp(-((u - 0.35) / 0.05) ** 2)[:, None] * 0.35
    col = col * (1 - fuller)
    img[y0:y1, x0:x1] = col[None]
    for k, (c, _, _) in FILL.items():
        y0, y1, x0, x1 = rect(img, sw[k]); img[y0:y1, x0:x1] = c


def mr(img):
    y0, y1, x0, x1 = rect(img, sw['steel'])
    u = np.clip((np.arange(x0, x1) - x0) / max(x1 - x0 - 1, 1), 0, 1)
    # steel like the armour plates (metal 0.5 / rough 0.58) but a little shinier toward the edge, so the blade
    # does not turn into a black mirror of a dark environment
    img[y0:y1, x0:x1, 0] = 1.0; img[y0:y1, x0:x1, 1] = (0.48 - 0.14 * u)[None]; img[y0:y1, x0:x1, 2] = 0.6
    for k, (_, metal, rough) in FILL.items():
        y0, y1, x0, x1 = rect(img, sw[k]); img[y0:y1, x0:x1] = (1.0, rough, metal)


def normal(img):
    for k in ('steel', *FILL):
        y0, y1, x0, x1 = rect(img, sw[k]); img[y0:y1, x0:x1] = (0.5, 0.5, 1.0)


for tier in 'abc':
    paint(f'gob_{tier}_basecolor.png', base)
for n in ('gob_metal_rough.png', 'gob_metal_rough_1k.png'):
    paint(n, mr)
for n in ('gob_normal.png', 'gob_normal_1k.png'):
    paint(n, normal)
print('PAINTED sword swatches', sw)
