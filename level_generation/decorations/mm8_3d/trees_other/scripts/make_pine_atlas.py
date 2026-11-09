#!/usr/bin/env python3
"""Pine needle atlas (shared/needles_pine_*): the shared needle atlas with its colour scaled per channel (linear) so
that the pines' darkness and hue live in the texture and their COLOR_0 tint stays near 1 (the vertex floor then
keeps needles well above black). SCALE = lin(reference pine target) / needle atlas frond-cell mean / TINT, with a
little extra blue (`BLUE`, the sprite's darker blue-green tiers). Normals are the shared needle normals (copied
byte-identical). Writes needles_pine.json (cells, means) for common.tints(). Usage: make_pine_atlas.py"""
import json, os, shutil
import numpy as np
from PIL import Image
import common
REF = np.array([115, 131, 21]) / 255.0        # tree29's needle target that matched the approved in-game darkness
TINT = 0.95
BLUE = 1.25
meta = common.atlas('needles')
cells = [0, 1, 2, 3]
w = np.array([meta['cells'][c]['coverage'] for c in cells])
mean = np.average([meta['cells'][c]['mean_linear'] for c in cells], axis=0, weights=w)
scale = common.lin(REF) / mean / TINT * np.array([1.0, 1.0, BLUE])
src = np.asarray(Image.open(common.shared_path('needles_basecolor.png')).convert('RGBA')).astype(np.float32) / 255
rgb = common.srgb(np.clip(common.lin(src[..., :3]) * scale, 0, 1))
out = np.dstack([rgb, src[..., 3]])
Image.fromarray((out * 255 + 0.5).astype(np.uint8), 'RGBA').save(common.shared_path('needles_pine_basecolor.png'))
shutil.copyfile(common.shared_path('needles_normal.png'), common.shared_path('needles_pine_normal.png'))
new = json.loads(json.dumps(meta))
for c in new['cells']:
    c['mean_linear'] = (np.array(c['mean_linear']) * scale).round(5).tolist()
json.dump(new, open(common.shared_path('needles_pine.json'), 'w'), indent=1)
print('PINE ATLAS scale (linear)', scale.round(3), 'frond mean sRGB', (common.srgb(mean * scale) * 255).round(0))
