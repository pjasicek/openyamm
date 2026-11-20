#!/usr/bin/env python3
"""Needle faces: a few zero-area lining slivers on the midline (3D area ~1e-6 m2) got UVs reaching to the atlas corner, so they crossed other
charts and Meshy painted their colour along thin lines over them. The faces are invisible (inside the skirt): drop them from work/uv.npz
(the original kept as work/uv_orig.npz) and write work/needle_mask.png (4K): the texels they covered that belong to other charts, which
compose_pf.py refills from the nearest good texel of the chart. Project folder."""
import shutil
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw
if not Path('work/uv_orig.npz').exists(): shutil.copy('work/uv.npz', 'work/uv_orig.npz')
D = dict(np.load('work/uv_orig.npz')); tri, uv, mat, co = D['tri'], D['uv'], D['mat'], D['co']
P = uv[tri]; e = np.max(np.linalg.norm(P - np.roll(P, 1, 1), axis=2), 1)
X = co[tri]; a3 = np.linalg.norm(np.cross(X[:, 1] - X[:, 0], X[:, 2] - X[:, 0]), axis=1) / 2
bad = ((e > 0.15) & (a3 < 1e-5)) | (a3 < 2e-7)      # needles and the zero-area midline slivers of the mirror
print('NEEDLES', int(bad.sum()), 'faces, max uv edge', round(float(e[bad].max()), 3) if bad.any() else 0, 'mats', np.unique(mat[bad]).tolist())
S = 4096
for m, name in ((0, 'needle_mask.png'), (1, 'needle_mask_head.png')):
    nb = Image.new('L', (S, S), 0); dn = ImageDraw.Draw(nb); ok = Image.new('L', (S, S), 0); do = ImageDraw.Draw(ok)
    for f in np.where(bad & (mat == m))[0]: dn.polygon([(float(uv[i, 0] * S), float((1 - uv[i, 1]) * S)) for i in tri[f]], fill=255, outline=255)
    for f in np.where(~bad & (mat == m))[0]: do.polygon([(float(uv[i, 0] * S), float((1 - uv[i, 1]) * S)) for i in tri[f]], fill=255)
    msk = (np.asarray(nb) > 0) & (np.asarray(ok) > 0)
    from scipy import ndimage
    msk = ndimage.binary_dilation(msk, iterations=2) & (np.asarray(ok) > 0)
    Image.fromarray((msk * 255).astype('u1')).save('work/' + name); print(name, int(msk.sum()), 'texels to refill')
keep = ~bad
D['tri'] = tri[keep]; D['mat'] = mat[keep]
if 'inner' in D: D['inner'] = D['inner'][keep]
np.savez('work/uv.npz', **D); print('UV faces', len(tri), '->', int(keep.sum()))
