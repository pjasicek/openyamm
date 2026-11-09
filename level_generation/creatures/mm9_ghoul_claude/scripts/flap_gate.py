#!/usr/bin/env python3
"""Thighs through the flaps, per clip at 48 fps: a flap vertex counts when it lies behind the skin of the thighs, hips and belly (under the nearest skin face, deeper than 3 mm beyond its own depth at rest). Args: <glb> <out json> [clips]"""
import json, sys
from pathlib import Path
import numpy as np
from scipy.spatial import cKDTree
HERE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE.parent / 'claude_shared' / 'floor')); sys.path.insert(0, str(HERE.parent / 'claude_shared'))
from glb_pose import Glb, Model
from detached_parts_audit import closest_on_triangles
glb, out = sys.argv[1:3]
want = sys.argv[3].split(',') if len(sys.argv) > 3 else None
m = Model(Glb(glb)); doc = m.glb.json
names = [doc['nodes'][j]['name'] for j in doc['skins'][0]['joints']]
ix = {n: i for i, n in enumerate(names)}
prims = [p for p in m.primitives]
keep_mesh = 0
Rs = m.skinned_positions(m.world({}))
offs = np.cumsum([0] + [len(r[0]) for r in Rs])
rest = np.concatenate([r[0] for r in Rs]); T = np.concatenate([np.asarray(r[1]).reshape(-1, 3) + o for r, o in zip(Rs, offs)])
J = np.concatenate([p['joints'] for p in prims]); W = np.concatenate([p['weights'] for p in prims])


def wt(n):
    if n not in ix: return np.zeros(len(rest))
    return ((J == ix[n]) * W).sum(1)


from scipy.spatial import cKDTree as _K
D = np.load(HERE / 'work' / 'flap_verts.npz'); LIFT = 1.1093
conv = lambda q: np.c_[q[:, 0], q[:, 2] + LIFT, -q[:, 1]]
w1 = (_K(conv(D['front'])).query(rest)[0] < 1e-3).astype(float)
w3 = (_K(conv(D['back'])).query(rest)[0] < 1e-3).astype(float)
thigh = sum(wt(f'Bip01 {s} {b}') for s in 'LR' for b in ('Thigh', 'Thigh_h', 'Calf', 'Calf_h')) * (1 - w1) if False else sum(wt(f'Bip01 {s} {b}') for s in 'LR' for b in ('Thigh_h', 'Calf', 'Calf_h'))
thigh = thigh * (1 - w1) * (1 - w3)
fl = {}
for nm, w, sgn in (('front', w1, 1), ('back', w3, -1)):
    f = np.where((w[T] > 0.5).all(1))[0]
    a, b, c = rest[T[f, 0]], rest[T[f, 1]], rest[T[f, 2]]
    n = np.cross(b - a, c - a)
    # outer faces only: the lining faces the body
    f = f[(n[:, 2] * sgn) > 0]
    fl[nm] = (f, sgn)
    print(nm, 'flap faces', len(f))
thigh = thigh + sum(wt(f'Bip01 {s} Thigh') for s in 'LR') * (1 - w1) * (1 - w3)
q = np.where(thigh > 0.25)[0]
fl_v = (w1 + w3) > 0
hd = ((J == ix['Bip01 Head']) * W).sum(1) > 0.5
sf = np.where(~fl_v[T].any(1) & (thigh[T] > 0.1).any(1) & (T.max(1) < len(prims[0]['positions']) if False else True))[0]
print('thigh verts', len(q))
res = {}
for a_ in doc['animations']:
    clip = a_['name']
    if want and clip not in want: continue
    dur = m.clip_times(clip)[-1]; TS = np.arange(0, dur + 1e-6, 1 / 48)
    rec = {}
    for nm, (cf, sgn) in fl.items():
        frames = 0; top = 0.0; tt = 0
        vs = np.unique(T[cf])
        base = None
        for t in [None] + list(TS):
            x = rest if t is None else np.concatenate([r[0] for r in m.skinned_positions(m.world(m.sample(clip, float(t))))])
            ft = x[T[sf]]
            c_ = ft.mean(1); n_ = np.cross(ft[:, 1] - ft[:, 0], ft[:, 2] - ft[:, 0]); n_ /= np.maximum(np.linalg.norm(n_, axis=1, keepdims=True), 1e-12)
            _, near = cKDTree(c_).query(x[vs], k=12)
            pts = np.repeat(x[vs], near.shape[1], 0)
            qq, bc = closest_on_triangles(pts, ft[near.ravel(), 0], ft[near.ravel(), 1], ft[near.ravel(), 2])
            dd = np.linalg.norm(pts - qq, axis=1).reshape(near.shape); b = dd.argmin(1); r = np.arange(len(vs))
            fid = near[r, b]; cp = qq.reshape(*near.shape, 3)[r, b]; v = x[vs] - cp
            s_ = np.einsum('ij,ij->i', v, n_[fid]); dist = dd[r, b]
            depth = np.where((s_ < 0) & (-s_ > 0.9 * dist) & (dist < 0.10), -s_, 0.0)
            if t is None:
                base = depth; continue
            inside = depth > base + 0.003
            if inside.any():
                frames += 1
                d = float((depth - base)[inside].max())
                if d > top: top = d; tt = float(t)
        rec[nm] = dict(frames=frames, of=len(TS), max_cm=round(top * 100, 1), at=round(tt, 3))
    res[clip] = rec
    print(f"{clip:15s} " + ' | '.join(f"{k} {v['frames']:3d}/{v['of']} {v['max_cm']:5.1f} cm at {v['at']:.2f}" for k, v in rec.items()), flush=True)
json.dump(res, open(out, 'w'), indent=1)
