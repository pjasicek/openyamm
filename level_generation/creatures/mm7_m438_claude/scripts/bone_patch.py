#!/usr/bin/env python3
"""Choose a 40 x 40 texel patch of free body-atlas texels (farthest from every UV island in work/uvraster_UVMap.npz)
for the stump bones' ivory (stump_bone.py maps them there, compose_m438.py paints it). Writes work/bone_patch.json."""
import json
from pathlib import Path
import numpy as np
from scipy import ndimage
HERE = Path(__file__).resolve().parents[1]
cov = np.load(HERE / 'work' / 'uvraster_UVMap.npz')['piece'] >= 0
d = ndimage.distance_transform_edt(~cov)
d[:24, :] = d[-24:, :] = 0; d[:, :24] = d[:, -24:] = 0
cy, cx = np.unravel_index(int(np.argmax(d)), d.shape)
patch = {'row': int(cy) - 20, 'col': int(cx) - 20, 'size': 40, 'atlas': int(cov.shape[0]), 'clearance_texels': float(d[cy, cx])}
(HERE / 'work' / 'bone_patch.json').write_text(json.dumps(patch))
print('PATCH', patch)
