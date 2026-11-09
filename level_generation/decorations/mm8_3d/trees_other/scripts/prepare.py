#!/usr/bin/env python3
"""Crown envelope of one species: work/<id>/profile.json = the restored sprite's half-width per height (both as
fractions of the sprite's opaque height), 51 rows, plus the horizontal centre offset per row (centre_by_height, a
fraction of the height: positive = right of the trunk base) for leaning trees. The bark and foliage maps are shared
(make_shared.py). Usage: prepare.py <id>"""
import json, os
import numpy as np
from PIL import Image
import common
spec = common.load(); W = spec['work']

sprite = np.asarray(Image.open(spec['sprite_path']).convert('RGBA'))
a = sprite[..., 3] > 128
rows = np.where(a.any(1))[0]; top, bottom = rows.min(), rows.max(); H = bottom - top + 1
base_cols = np.where(a[bottom - 2:bottom + 1].any(0))[0]
base_x = (base_cols.min() + base_cols.max()) / 2
profile, centre = [], []
for k in range(51):
    y = int(bottom - k / 50 * (H - 1))
    cols = np.where(a[y])[0]
    profile.append([k / 50, float((cols.max() - cols.min() + 1) / 2 / H) if cols.size else 0.0])
    centre.append([k / 50, float(((cols.max() + cols.min()) / 2 - base_x) / H) if cols.size else 0.0])
json.dump({'height_px': int(H), 'width_px': int(a.any(0).sum()), 'half_width_by_height': profile,
           'centre_by_height': centre}, open(os.path.join(W, 'profile.json'), 'w'), indent=1)
print('PROFILE', [(p[0], round(p[1], 3)) for p in profile[::5]])
