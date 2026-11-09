#!/usr/bin/env python3
"""Colour tiers of the limbs: one shared set (tier C's paint) + region mask + ramps. Regions: R skin (hue, saturation), G the rest (wraps, rope, sandals, shorts). Ramps fitted against each tier's own paint on this same layout.
Writes textures/thrall_limbs_final.png, thrall_region_mask.png, thrall_ramps.json."""
import json, sys
from pathlib import Path
import numpy as np
from PIL import Image
from scipy import ndimage
sys.path.insert(0, '../claude_shared')
import region_variants as RV
T = Path('textures')
load = lambda p: np.asarray(Image.open(p).convert('RGB'), np.float32) / 255
base = load(T / 'thrall_limbs_c_soft.png')
tiers = {f'thrall_{t}': load(T / f'thrall_limbs_{t}_soft.png') for t in 'abc'}
Image.fromarray((base * 255 + .5).astype('u1')).save(T / 'thrall_limbs_final.png')
mx, mn = base.max(2), base.min(2); sat = (mx - mn) / np.maximum(mx, 1e-6)
r, g, b = base[..., 0], base[..., 1], base[..., 2]
hue = np.degrees(np.arctan2(np.sqrt(3) * (g - b), 2 * r - g - b)) % 360
skin = (hue > 12) & (hue < 33) & (sat > 0.3) & (mx > 0.3)
skin = ndimage.binary_opening(ndimage.binary_closing(skin, iterations=3), iterations=2)
ws = np.clip(ndimage.gaussian_filter(skin.astype(np.float32), 1.5) * 1.2, 0, 1)
wr = 1 - ws
ramps = {v: [] for v in tiers}
for name, w in (('skin', ws), ('gear', wr)):
    rp, err = RV.fit_ramps(base, tiers, w)
    print('RAMPS', name, json.dumps(err)[:300])
    for v in tiers: ramps[v].append(rp[v])
RV.write_mask([ws, wr], T / 'thrall_region_mask.png', 1024)
json.dump({'variants': list(tiers), 'materials': [{'base': 'Thrall', 'prefix': 'Thrall', 'mask': 'thrall_region_mask.png', 'ramps': ramps}]}, open(T / 'thrall_ramps.json', 'w'))
print('RAMPS done, skin share', float(ws.mean()))
