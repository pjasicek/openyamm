"""Sliver drift (m352, the playbook's "UV corner pushed onto a chart border" case that the per-face median of
texture_drift.py misses): SLIVER_SAMPLES (default 40) samples per face, a face is flagged when at least NBAD of them differ from the
source colour at the same rest point by more than THRESH (0-255) and the nearest source face is visible
(work/visible_all.npy). Optionally locks the source faces within REA_LOCK_R of flagged faces into a keep array.
Usage: sliver_check.py <tag> [<base keep .npy or -> <out keep .npy>]"""
import sys
import numpy as np
from PIL import Image
from scipy.spatial import cKDTree

tag = sys.argv[1]
img = np.asarray(Image.open('work/basecolor.png').convert('RGB'), np.float32)
H, W = img.shape[:2]
rng = np.random.default_rng(1)
B = rng.dirichlet((1, 1, 1), int(__import__("os").environ.get("SLIVER_SAMPLES", "40")))  # barycentric samples per face


def samples(path):
    d = np.load(path); v, f, uv = d['verts'], d['faces'], d['wuv'].reshape(-1, 3, 2)
    tri = v[f]; nrm = np.cross(tri[:, 1] - tri[:, 0], tri[:, 2] - tri[:, 0])
    nrm /= np.linalg.norm(nrm, axis=1, keepdims=True) + 1e-12
    pos = np.einsum('sk,fkc->fsc', B, tri); u = np.einsum('sk,fkc->fsc', B, uv)
    x = np.clip((u[..., 0] % 1) * W, 0, W - 1).astype(int); y = np.clip((1 - u[..., 1] % 1) * H, 0, H - 1).astype(int)
    return pos, nrm, img[y, x], tri


sp, sn, sc, _ = samples('work/mesh_in.npz')
cp, cn, cc, ctri = samples(f'work/mesh_{tag}.npz')
tree = cKDTree(sp.reshape(-1, 3))
k = 8
dist, idx = tree.query(cp.reshape(-1, 3), k)
srcn = np.repeat(sn, len(B), 0)[idx]  # (N, k, 3)
cnr = np.repeat(cn, len(B), 0)[:, None]
ok = np.abs((srcn * cnr).sum(-1)) > .5  # two-sided cards: either orientation
dist = np.where(ok, dist, np.inf)
best = idx[np.arange(len(idx)), dist.argmin(1)]
diff = np.abs(cc.reshape(-1, 3) - sc.reshape(-1, 3)[best]).mean(1).reshape(len(cn), len(B))
THRESH, NBAD = float(__import__('os').environ.get('SLIVER_THRESH', '60')), int(__import__('os').environ.get('SLIVER_N', '3'))
nb = (diff > THRESH).sum(1)
area = np.linalg.norm(np.cross(ctri[:, 1] - ctri[:, 0], ctri[:, 2] - ctri[:, 0]), axis=1) / 2
cen = ctri.mean(1)
src = np.load('work/mesh_in.npz'); scen = src['verts'][src['faces']].mean(1); stree = cKDTree(scen)
vis = np.load('work/visible_all.npy')[stree.query(cen)[1]] > 0
bad = (nb >= NBAD) & vis & (area * 1e4 > float(__import__('os').environ.get('SLIVER_MIN_CM2', '1')))
print(tag, 'sliver faces', int(bad.sum()), 'area cm2', round(float(area[bad].sum() * 1e4), 1))
for fi in np.argsort(-nb * bad)[:12]:
    if bad[fi]:
        print('  face', fi, 'samples off', int(nb[fi]), 'area %.2fcm2' % (area[fi] * 1e4), 'at', np.round(cen[fi], 3))
if len(sys.argv) > 3:
    import os
    keep = np.zeros(len(scen), bool) if sys.argv[2] == '-' else np.load(sys.argv[2]).copy(); n0 = int(keep.sum())
    R = float(os.environ.get('REA_LOCK_R', '0.02'))
    for c in cen[bad]:
        keep[stree.query_ball_point(c, R)] = True
    np.save(sys.argv[3], keep); print('LOCK kept faces', n0, '->', int(keep.sum()))
