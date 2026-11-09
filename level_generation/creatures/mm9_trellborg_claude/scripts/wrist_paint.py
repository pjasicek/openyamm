#!/usr/bin/env python3
"""The wrist band's texels (paint smeared over the old groove) take the hand's own skin, per tier, by angle round the arm, colour and normal, so bracer and hand meet in one skin. Overwrites textures/trell_body_{t}_final.png and _normal.png once: originals kept as *_prewrist.png."""
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
    band = arm & (al > -0.004) & (al < 0.075); src = arm & (al > 0.085) & (al < 0.125) & (r > 0.03)
    k = lambda m, a: np.c_[np.cos(th[m]) * 0.07, np.sin(th[m]) * 0.07, a]
    tr = cKDTree(k(src, al[src] * 0.25))
    ys, xs = np.nonzero(src); yb, xb = np.nonzero(band)
    rng = np.random.default_rng(7); i = rng.integers(0, len(ys), len(yb))
    ix[S] = (yb, xb, ys, xs, i, np.clip((al[band] + 0.004) / 0.012, 0, 1)); print('WRISTPAINT', S, len(yb))
for t in 'abc':
    for nm, sc in (('final', 1), ('normal', 2), ('orm', 2)):
        p = Path(f'textures/trell_body_{t}_{nm}.png'); o = p.with_name(p.stem + '_prewrist.png')
        if not o.exists(): shutil.copyfile(p, o)
        a = np.asarray(Image.open(o).convert('RGB'), np.float32).copy()
        from scipy import ndimage
        for yb, xb, ys, xs, i, w in ix.values():
            m_ = a[ys // sc, xs // sc].mean(0)                         # hand skin only, one tone, its own fine grain
            g_ = a[ys[i] // sc, xs[i] // sc] - m_
            lay = np.zeros(a.shape, np.float32); lay[yb // sc, xb // sc] = g_
            lay = ndimage.gaussian_filter(lay, (0.8, 0.8, 0))
            tgt = (m_ + lay[yb // sc, xb // sc] * (2.0 if nm == 'final' else 0.0)) if nm != 'normal' else np.array([128, 128, 255], np.float32)
            a[yb // sc, xb // sc] = a[yb // sc, xb // sc] * (1 - w[:, None]) + tgt * w[:, None]
            if nm == 'orm': a[yb // sc, xb // sc, 0] = 255        # no baked occlusion line at the join
        Image.fromarray(a.astype('u1')).save(p)
print('WRISTPAINT done')
