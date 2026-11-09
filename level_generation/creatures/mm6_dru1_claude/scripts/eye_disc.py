#!/usr/bin/env python3
"""Free squares in the head atlas for the two eye patches (eye_uv.py, compose_dru1.py): free texels at least PAD px from
any covered texel (work/uvraster_HeadUV.npz, eye caps excluded), two SIZE-px squares far apart. Writes
work/eye_disc.json {'size': px, 'squares': [[x0, y0], [x0, y0]]} (pixel origins, top-left, image rows down)."""
import json
from pathlib import Path
import numpy as np
from scipy import ndimage
HERE = Path(__file__).resolve().parents[1]
R = np.load(HERE / 'work' / 'uvraster_HeadUV.npz')
cov = R['piece'] >= 0
N = cov.shape[0]; SIZE, PAD = 32, 2
free = ~ndimage.binary_dilation(cov, iterations=PAD)
# a square fits where the box filter of free over SIZE is all free
ec = R['eye'] if 'eye' in R.files else None
ok = ndimage.binary_erosion(free, structure=np.ones((SIZE, SIZE), bool), border_value=0)   # box centres
ys, xs = np.nonzero(ok); ys = ys - SIZE // 2; xs = xs - SIZE // 2                         # -> top-left origins
if len(ys) == 0:
    raise SystemExit('no free square')
k = int(np.argmax(ys + xs)); a = (int(xs[k]), int(ys[k]))
far = (np.abs(xs - a[0]) >= SIZE + PAD) | (np.abs(ys - a[1]) >= SIZE + PAD)
k2 = int(np.argmax(np.where(far, ys + xs, -1))); b = (int(xs[k2]), int(ys[k2]))
(HERE / 'work' / 'eye_disc.json').write_text(json.dumps({'size': SIZE, 'squares': [a, b]}))
print('EYESQUARES', a, b, SIZE)
