#!/usr/bin/env python3
"""Crown envelope for one species: work/<id>/profile.json = the restored x2 sprite's half-width per height (both as
fractions of the tree height), plus the trunk's half-width near the ground. Bark and leaf maps are shared
(make_shared.py). Usage: prepare.py <id>"""
import json, os
import numpy as np
from PIL import Image
import common
spec = common.load(); W = spec['work']
sprite = np.asarray(Image.open(spec['sprite_path']).convert('RGBA'))
a = sprite[..., 3] > 128
rows = np.where(a.any(1))[0]; top, bottom = rows.min(), rows.max(); H = bottom - top + 1
cols_all = np.where(a.any(0))[0]
profile = []
for k in range(51):
    y = int(bottom - k / 50 * (H - 1))
    cols = np.where(a[y])[0]
    profile.append([k / 50, float((cols.max() - cols.min() + 1) / 2 / H) if cols.size else 0.0])
trunk = np.where(a[bottom - int(0.06 * H)])[0]
json.dump({'height_px': int(H), 'width_px': int(cols_all.max() - cols_all.min() + 1),
           'trunk_half_width': float((trunk.max() - trunk.min() + 1) / 2 / H) if trunk.size else 0.0,
           'half_width_by_height': profile}, open(os.path.join(W, 'profile.json'), 'w'), indent=1)
print('PROFILE', [(p[0], round(p[1], 3)) for p in profile[::5]], 'trunk', round((trunk.max() - trunk.min() + 1) / 2 / H, 3))
