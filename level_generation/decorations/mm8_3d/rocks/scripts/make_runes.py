#!/usr/bin/env python3
"""Carved rune masks for the rune stones, traced from the native x2 sprite: inside each rune box (sprite pixels),
pixels much darker than their surroundings and not green or orange (leaves, vine) become strokes. The mask covers
the rock's sprite_box (rocks.json), so build_rock.py projects it straight onto the stone's front.
Writes textures/runes_<rock>.png (white strokes). Usage: make_runes.py <rock>..."""
import json
import os
import sys

import numpy as np
from PIL import Image, ImageFilter

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REPO = os.path.abspath(os.path.join(HERE, '..', '..', '..', '..'))
CFG = json.load(open(os.path.join(HERE, 'scripts', 'rocks.json')))
INV = {e['name']: e for e in json.load(open(os.path.join(HERE, '..', 'inventory.json')))}

for rock in sys.argv[1:]:
    cfg = CFG[rock]; runes = cfg['runes']
    live = os.path.join(REPO, 'assets_dev', 'engine', 'decorations_x2', INV[rock]['files'][0])
    if not os.path.exists(live):                 # retired 2026-10-16: the archive, read only
        live = os.path.join(REPO, 'assets_legacy', 'decorations_x2_mm8_20261016', INV[rock]['files'][0])
    im = Image.open(live).convert('RGBA')
    scale = 4                                    # trace at 4x for smooth strokes
    big = im.resize((im.width * scale, im.height * scale), Image.BICUBIC)
    a = np.asarray(big).astype(np.float32) / 255
    rgb = a[..., :3]
    luma = rgb @ np.array([0.299, 0.587, 0.114], np.float32)
    local = np.asarray(Image.fromarray((luma * 255).astype(np.uint8)).filter(
        ImageFilter.BoxBlur(runes.get('radius', 7) * scale))).astype(np.float32) / 255
    r, g, b = rgb[..., 0], rgb[..., 1], rgb[..., 2]
    green = g > r * 1.08
    orange = (r > g * 1.35) & (r > 0.35)
    stroke = np.clip((local - luma - runes.get('threshold', 0.08)) / 0.08, 0, 1) * (~green) * (~orange)
    stroke *= luma < runes.get('max_luma', 0.42)
    box_mask = np.zeros_like(luma)
    for x0, y0, x1, y1 in runes['boxes']:
        box_mask[y0 * scale:y1 * scale, x0 * scale:x1 * scale] = 1
    stroke *= box_mask
    m = Image.fromarray((stroke * 255).astype(np.uint8)).filter(ImageFilter.MedianFilter(5))
    o = runes.get('open', 0)                     # opening removes isolated specks of dark stone grain
    if o:
        m = m.filter(ImageFilter.MinFilter(o)).filter(ImageFilter.MaxFilter(o))
    m = m.filter(ImageFilter.GaussianBlur(scale * 0.5))
    x0, x1, yt, yb = cfg['sprite_box']
    m = m.crop((x0 * scale, yt * scale, x1 * scale, yb * scale))
    m = m.point(lambda v: 255 if v > 90 else int(v * 255 / 90))
    out = os.path.join(HERE, 'textures', f'runes_{rock}.png')
    m.save(out)
    print('RUNES', out, m.size, 'coverage', round(float((np.asarray(m) > 128).mean()), 4))
