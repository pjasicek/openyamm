#!/usr/bin/env python3
"""Rest-pose surface error of decimated meshes per region, without Blender (fast ratio sweeps; the heads are rigid on
their Head bones, so their rest error is their error in every clip). Both directions: source vertices -> candidate
surface and candidate vertices -> source surface, surfaces sampled at about 1.5 mm spacing. Each point is counted in
the region (groups.npy label, 'keep' for kept faces) of the nearest source face.
Usage: rest_error.py <groups.npy> <keep.npy> <tag,...> [limit mm, default 6]"""
import sys
import numpy as np
from scipy.spatial import cKDTree

groups, keep = np.load(sys.argv[1]), np.load(sys.argv[2]); tags = sys.argv[3].split(',')
LIM = float(sys.argv[4]) / 1000 if len(sys.argv) > 4 else .006
s = np.load('work/mesh_in.npz'); sv, sf = s['verts'], s['faces']
label = np.where(keep, -1, groups)


def sample(v, f, step=.0015):
    t = v[f]; a = np.linalg.norm(np.cross(t[:, 1] - t[:, 0], t[:, 2] - t[:, 0]), axis=1) / 2
    n = np.clip((a / step ** 2).astype(int), 1, 400); idx = np.repeat(np.arange(len(f)), n)
    r = np.random.default_rng(0).random((len(idx), 2)); flip = r.sum(1) > 1; r[flip] = 1 - r[flip]
    p = t[idx, 0] + r[:, :1] * (t[idx, 1] - t[idx, 0]) + r[:, 1:] * (t[idx, 2] - t[idx, 0])
    return np.concatenate([p, v]), np.concatenate([idx, np.full(len(v), -1)])


sp, sfi = sample(sv, sf); stree = cKDTree(sp)
# source vertex -> its faces' label (first face)
vf = np.full(len(sv), -1); vf[sf.reshape(-1)[::-1]] = np.repeat(np.arange(len(sf)), 3)[::-1]
fcen = cKDTree(sv[sf].mean(1))
for tag in tags:
    c = np.load(f'work/mesh_{tag}.npz'); cv, cf = c['verts'], c['faces']
    cp, _ = sample(cv, cf); ctree = cKDTree(cp)
    d1, _ = ctree.query(sv)                       # source vertex -> candidate surface
    d2, _ = stree.query(cv)                        # candidate vertex -> source surface
    l1 = label[vf]; l2 = label[fcen.query(cv)[1]]
    d, l = np.concatenate([d1, d2]), np.concatenate([l1, l2])
    rows = []
    for g in sorted(set(l.tolist())):
        m = l == g
        rows.append(f'{g}:{int((d[m] > LIM).sum())}/{m.sum()} max {d[m].max() * 1000:.0f}')
    print(f'REST {tag} tris {len(cf)} p99 {np.percentile(d, 99) * 1000:.1f} max {d.max() * 1000:.1f} | ' + ' | '.join(rows))
