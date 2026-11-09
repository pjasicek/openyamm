#!/usr/bin/env python3
"""Hair through the robe, per clip at 48 fps (female Honk): true intersection, a braid or veil-strand edge crossing a body cloth triangle, and how far the
tip beyond the crossing stands out of the cloth. Parts: loose hair parts weighted to Ponytail or Y chains. Reports per clip: frames, worst edge count, worst
height, worst part and rest height along it, so a fix can name the stretch of braid. Args: <glb> <out json> [clips]"""
import json, sys
from pathlib import Path
import numpy as np
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import connected_components
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'claude_shared' / 'floor'))
from glb_pose import Glb, Model
glb, out = sys.argv[1:3]
want = sys.argv[3].split(',') if len(sys.argv) > 3 else None
m = Model(Glb(glb)); doc = m.glb.json
names = [doc['nodes'][j]['name'] for j in doc['skins'][0]['joints']]
prims = [p for p in m.primitives if p['skinned']]
off = np.cumsum([0] + [len(p['positions']) for p in prims])
T = np.vstack([p['triangles'] + off[i] for i, p in enumerate(prims)])
J = np.vstack([p['joints'] for p in prims]); W = np.vstack([p['weights'] for p in prims]); P = np.vstack([p['positions'] for p in prims])
idx = [i for i, p in enumerate(m.primitives) if p['skinned']]
hairb = [i for i, n in enumerate(names) if 'Ponytail' in n or n.startswith('Y')]
_, inv = np.unique(np.round(P, 4), axis=0, return_inverse=True); inv = inv.ravel()
e = np.r_[inv[T[:, [0, 1]]], inv[T[:, [1, 2]]], inv[T[:, [0, 2]]]]
n, cl = connected_components(coo_matrix((np.ones(len(e)), (e[:, 0], e[:, 1])), shape=(inv.max() + 1, inv.max() + 1)), directed=False)
part = cl[inv]
hw = np.where(np.isin(J, hairb), W, 0).sum(1)
share = np.bincount(part, hw) / np.maximum(np.bincount(part), 1)
hairp = np.where((share > 0.04) & (np.bincount(part) > 30) & (np.bincount(part) < 500))[0]
fp = part[T[:, 0]]
hf = np.where(np.isin(fp, hairp))[0]
tu = None
armb = [i for i, nm in enumerate(names) if any(s in nm for s in ('Forearm', 'Hand', 'Finger', 'Thumb', 'Index', 'Middle', 'Ring', 'Pinky'))]
fw = np.zeros((len(T), len(names)))
for k in range(J.shape[1]):
    for c in range(3):
        np.add.at(fw, (np.arange(len(T)), J[T[:, c], k]), W[T[:, c], k])
isarm = fw[:, armb].sum(1) > 1.5
y = P[T].mean(1)[:, 1]
top = P[:, 1].max()
head = fw[:, names.index('Bip01 Head')] > 1.5
body_mat = np.arange(len(T)) < len(prims[0]['triangles'])      # the head set's hidden neck skirt is not cloth
cloth = np.where(body_mat & ~np.isin(fp, hairp) & ~head & ~isarm & (y > 0.9) & (y < 1.55))[0]
print('hair parts', len(hairp), 'hair faces', len(hf), 'cloth faces', len(cloth))
ed = np.unique(np.sort(np.r_[T[hf][:, [0, 1]], T[hf][:, [1, 2]], T[hf][:, [0, 2]]], axis=1), axis=0)
# only the part of the hair that can reach the robe
ed = ed[P[ed].min(1)[:, 1] < 1.5]
res = {}
for clip in [a['name'] for a in doc['animations']]:
    if want and clip not in want:
        continue
    dur = m.clip_times(clip)[-1]
    times = np.arange(0, dur + 1e-6, 1 / 48)
    fr, wc, wt, wh, wr = 0, 0, 0, None, None
    for ti, t in enumerate(times):
        world = m.world(m.sample(clip, float(t)))
        x = np.vstack([s[0] for s, p in zip(m.skinned_positions(world), m.primitives) if p['skinned']])
        o = x[ed[:, 0]][:, None]; d = (x[ed[:, 1]] - x[ed[:, 0]])[:, None]
        A = x[T[cloth, 0]][None]; e1 = x[T[cloth, 1]][None] - A; e2 = x[T[cloth, 2]][None] - A
        h = np.cross(d, e2); det = (e1 * h).sum(2); s = o - A
        with np.errstate(divide='ignore', invalid='ignore'):
            u = (s * h).sum(2) / det; q = np.cross(s, e1); v = (d * q).sum(2) / det; tt = (e2 * q).sum(2) / det
        hit = (np.abs(det) > 1e-12) & (u >= 0) & (v >= 0) & (u + v <= 1) & (tt >= 0) & (tt <= 1)
        c = int(hit.any(1).sum())
        if c:
            fr += 1
            if c > wc:
                ee = np.nonzero(hit.any(1))[0]
                wc, wt, wh, wr = c, ti, round(float(x[ed[ee]][:, :, 1].mean()), 3), round(float(P[ed[ee]][:, :, 1].min()), 3)
    res[clip] = dict(frames=fr, of=len(times), worst_edges=wc, at_frame=wt, height=wh, rest_height=wr)
    print(f'{clip:13} {fr:3d}/{len(times):3d} frames, worst {wc:3d} edges @f{wt} height {wh} rest {wr}', flush=True)
json.dump(res, open(out, 'w'), indent=1)
