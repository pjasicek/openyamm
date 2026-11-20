"""Small colour flecks of a decimated mesh that texture_drift.py's per-face median misses (a pale chart-border
sliver on the green mantle, pale lines on the knuckles): 48 sample points per face, each against the nearest source
sample with a similar normal; a face is a fleck when at least REA_FLECK_N (4) samples differ by more than 80 (0-255,
mean of RGB). With <base keep .npy> <out .npy>, the source faces within REA_LOCK_R (0.02 m) of each fleck are added
to the keep set. Usage: fleck_check.py <tag> [<base keep .npy> <out .npy>]"""
import os
import sys
import numpy as np
from PIL import Image
from scipy.spatial import cKDTree

tag = sys.argv[1]
img = np.asarray(Image.open('work/basecolor.png').convert('RGB'), np.float32); H, W = img.shape[:2]
B = np.random.default_rng(2).dirichlet((1, 1, 1), 48)


def samples(path):
    d = np.load(path); v, f, uv = d['verts'], d['faces'], d['wuv'].reshape(-1, 3, 2)
    tri = v[f]; nrm = np.cross(tri[:, 1] - tri[:, 0], tri[:, 2] - tri[:, 0])
    nrm /= np.linalg.norm(nrm, axis=1, keepdims=True) + 1e-12
    pos = np.einsum('sk,fkc->fsc', B, tri); u = np.einsum('sk,fkc->fsc', B, uv)
    x = np.clip((u[..., 0] % 1) * W, 0, W - 1).astype(int); y = np.clip((1 - u[..., 1] % 1) * H, 0, H - 1).astype(int)
    return pos, nrm, img[y, x], tri


sp, sn, sc, stri = samples('work/mesh_in.npz')
cp, cn, cc, ctri = samples(f'work/mesh_{tag}.npz')
dist, idx = cKDTree(sp.reshape(-1, 3)).query(cp.reshape(-1, 3), 8)
ok = np.abs((np.repeat(sn, len(B), 0)[idx] * np.repeat(cn, len(B), 0)[:, None]).sum(-1)) > .5
best = idx[np.arange(len(idx)), np.where(ok, dist, np.inf).argmin(1)]
diff = np.abs(cc.reshape(-1, 3) - sc.reshape(-1, 3)[best]).mean(1).reshape(len(cn), len(B))
n_bad = (diff > 80).sum(1); fleck = n_bad >= int(os.environ.get('REA_FLECK_N', '4'))
cen = ctri.mean(1)
print(tag, 'fleck faces', int(fleck.sum()))
for i in np.where(fleck)[0][np.argsort(-n_bad[fleck])][:30]:
    print(f'  face {i} samples {n_bad[i]}/48 at {np.round(cen[i], 3)}')
np.save(f'work/fleck_{tag}.npy', fleck)
if len(sys.argv) > 3:
    keep = np.load(sys.argv[2]).copy(); scen = stri.mean(1)
    near = cKDTree(scen).query_ball_point(cen[fleck], float(os.environ.get('REA_LOCK_R', '0.02')))
    for lst in near:
        keep[lst] = True
    np.save(sys.argv[3], keep); print('LOCK', int(np.load(sys.argv[2]).sum()), '->', int(keep.sum()))
