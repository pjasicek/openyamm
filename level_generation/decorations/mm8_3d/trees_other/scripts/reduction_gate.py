#!/usr/bin/env python3
"""Reduction gates for one species (after build.sh): LOD0 coverage and mean colour against the baseline
(work/<id>/before_stats.json, lod_check.py <id> before, rendered from the previous build with the same camera),
the largest colour step between neighbouring levels and each level's coverage; writes review/<id>/before_after.png
(review/<id>/before_sheet.png above the new sheet.png). Usage: reduction_gate.py <id>"""
import json, os
import numpy as np
from PIL import Image, ImageDraw
import common
spec = common.load(); W = spec['work']; R = spec['review']
before = json.load(open(os.path.join(W, 'before_stats.json')))
after = json.load(open(os.path.join(W, 'lc_stats.json')))
names = ['Tree', 'Tree_LOD1', 'Tree_LOD2', 'Tree_LOD3']


def fill(path):
    """Opaque pixels / (opaque bbox height)^2: coverage independent of the camera framing."""
    x = np.asarray(Image.open(path).convert('RGBA'))[..., 3] > 128
    rows = np.where(x.any(1))[0]
    return x.sum() / float(rows.max() - rows.min() + 1) ** 2


f_before = fill(os.path.join(W, 'before_common_Tree_eye.png'))
f_after = fill(os.path.join(W, 'lc_common_Tree_eye.png'))
f_sprite = fill(spec['sprite_path'])
cov = f_after / f_before - 1
print(f"FILL before {f_before:.3f} after {f_after:.3f} sprite {f_sprite:.3f}")
col = np.abs(np.array(after['Tree']['mean_rgb']) - np.array(before['Tree']['mean_rgb'])).max()
step = max(max(after[n].get('mean_diff_vs_previous', [0])) for n in names)
print(f"GATE {spec['id']} LOD0 coverage {cov:+.3f} colour {col:.1f} /255 step {step:.1f} coverage by LOD",
      [after[n]['coverage_vs_lod0'] for n in names])
top = Image.open(os.path.join(R, 'before_sheet.png')).convert('RGB')
low = Image.open(os.path.join(R, 'sheet.png')).convert('RGB')
w = max(top.width, low.width)
top = top.resize((w, int(top.height * w / top.width))); low = low.resize((w, int(low.height * w / low.width)))
sheet = Image.new('RGB', (w, top.height + low.height + 40), (150, 160, 175)); d = ImageDraw.Draw(sheet)
sheet.paste(top, (0, 20)); sheet.paste(low, (0, top.height + 40))
d.text((6, 4), 'BEFORE', fill=(0, 0, 0)); d.text((6, top.height + 24), 'AFTER', fill=(0, 0, 0))
sheet.save(os.path.join(R, 'before_after.png'))
