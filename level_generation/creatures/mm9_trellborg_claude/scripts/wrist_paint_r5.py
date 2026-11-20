#!/usr/bin/env python3
"""The r5 wrist paint, kept as installed: band texels take the hand's skin by angle round the arm, colour and normal; ORM untouched. Reads the *_prewrist.png originals."""
import json, shutil
from pathlib import Path
import numpy as np
from PIL import Image
from scipy.spatial import cKDTree
J = json.load(open('work/hands_v1.json'))['frames']
Z = np.load('work/body_pos.npz'); pos, cov = Z['pos'], Z['cov']
ix = {}
for S, sg in (('R', -1), ('L', 1)):
    W = np.array(J[S]['W']); d = np.array(J[S]['d']); d /= np.linalg.norm(d)
    U = np.cross(d, [0, 0, 1.0]); U /= np.linalg.norm(U); V = np.cross(d, U)
    rel = pos - W; al = rel @ d; x = rel @ U; y = rel @ V; th = np.arctan2(y, x); r = np.hypot(x, y)
    arm = cov & (np.sign(pos[..., 0]) == sg) & (r < 0.14)
    band = arm & (al > 0.001) & (al < 0.056); src = arm & (al > 0.06) & (al < 0.1) & (r > 0.03)
    k = lambda m, a: np.c_[np.cos(th[m]) * 0.07, np.sin(th[m]) * 0.07, a]
    tr = cKDTree(k(src, al[src] * 0.25)); _, i = tr.query(k(band, 0.0175 + (al[band] - 0.03) * 0.25), k=1)
    ys, xs = np.nonzero(src); yb, xb = np.nonzero(band)
    ix[S] = (yb, xb, ys[i], xs[i], np.clip(al[band] / 0.008, 0, 1))
for t in 'abc':
    for nm, sc in (('final', 1), ('normal', 2)):
        p = Path(f'textures/trell_body_{t}_{nm}.png'); a = np.asarray(Image.open(p.with_name(p.stem + '_prewrist.png')).convert('RGB'), np.float32).copy()
        for yb, xb, ys, xs, w in ix.values():
            a[yb // sc, xb // sc] = a[yb // sc, xb // sc] * (1 - w[:, None]) + a[ys // sc, xs // sc] * w[:, None]
        Image.fromarray(a.astype('u1')).save(p)
    shutil.copyfile(f'textures/trell_body_{t}_orm_prewrist.png', f'textures/trell_body_{t}_orm.png')
print('WRISTPAINT r5 done')
