#!/usr/bin/env python3
"""Compare two runtime GLBs of one creature (texture pass 2026-10-30): what changed besides the intended part.

Usage: glb_diff.py <before.glb> <after.glb> [--fps 48] [--ignore-box x0,y0,z0,x1,y1,z1 ...]
Reports: animation names, key counts and the largest key difference per clip; LOD0 triangle/vertex counts per
primitive; image sizes and whether each image's bytes changed; and, when both LOD0 primitives have the same vertex
count, the largest posed vertex distance per clip sampled at --fps (vertices whose rest position lies in an
--ignore-box, glTF coordinates, are left out: the part that was meant to change). Equal vertex counts are compared
index by index (vertices that moved at rest are reported apart); otherwise every after vertex is matched to its
nearest before vertex at rest (within 0.1 mm) with the most similar skin weights (UV-seam twins).
"""
import argparse, hashlib, os, sys
import numpy as np
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), *(['..'] * 2), 'claude_shared', 'floor'))
from glb_pose import Glb, Model
from scipy.spatial import cKDTree

ap = argparse.ArgumentParser()
ap.add_argument('before'); ap.add_argument('after')
ap.add_argument('--fps', type=float, default=48.0)
ap.add_argument('--ignore-box', action='append', default=[])
o = ap.parse_args()
A, B = Glb(o.before), Glb(o.after)
MA, MB = Model(A), Model(B)
boxes = [np.array([float(x) for x in b.split(',')]).reshape(2, 3) for b in o.ignore_box]


def images(g):
    out = {}
    for i, im in enumerate(g.json.get('images', [])):
        bv = g.json['bufferViews'][im['bufferView']]
        data = bytes(g.bin[bv.get('byteOffset', 0):bv.get('byteOffset', 0) + bv['byteLength']])
        out[im.get('name', str(i))] = hashlib.sha1(data).hexdigest()[:12]
    return out


ia, ib = images(A), images(B)
for k in sorted(set(ia) | set(ib)):
    print('image', k, 'same' if ia.get(k) == ib.get(k) else f'{ia.get(k)} -> {ib.get(k)}')
for ma in A.json['meshes']:
    mb = next((m for m in B.json['meshes'] if m.get('name') == ma.get('name')), None)
    ca = [A.json['accessors'][p['attributes']['POSITION']]['count'] for p in ma['primitives']]
    cb = [B.json['accessors'][p['attributes']['POSITION']]['count'] for p in mb['primitives']] if mb else None
    print('mesh', ma.get('name'), 'vertices', ca, '->', cb)
for clip in MA.clips:
    if clip not in MB.clips:
        print('clip', clip, 'MISSING after'); continue
    ta, tb = MA.clip_times(clip), MB.clip_times(clip)
    print('clip', clip, 'keys', len(ta), '->', len(tb), 'duration', round(ta[-1], 4), '->', round(tb[-1], 4))
pa = MA.primitives
pb = MB.primitives
rest_a = np.concatenate([p['positions'] for p in pa])
rest_b = np.concatenate([p['positions'] for p in pb])
keep = np.ones(len(rest_b), bool)
for bx in boxes:
    keep &= ~np.all((rest_b >= bx[0]) & (rest_b <= bx[1]), axis=1)
if len(rest_a) == len(rest_b):                        # same layout: compare vertex by vertex
    idx = np.arange(len(rest_b))
    d = np.linalg.norm(rest_b - rest_a, axis=1)
else:                                                 # nearest rest vertex with the same skin (UV-seam twins)
    def skin(prims, model):
        out = []
        for p in prims:
            m = np.zeros((len(p['positions']), len(model.joints)))
            if p['skinned']:
                np.put_along_axis(m, p['joints'], p['weights'], axis=1)
            out.append(m)
        return np.concatenate(out)
    sa, sb = skin(pa, MA), skin(pb, MB)
    dk, ik = cKDTree(rest_a).query(rest_b, k=8)
    wd = np.abs(sa[ik] - sb[:, None, :]).sum(-1) + (dk > 1e-4) * 1e3
    best = wd.argmin(1)
    idx, d = ik[np.arange(len(ik)), best], dk[np.arange(len(dk)), best]
match = keep & (d < 1e-4)
print('LOD0 vertices', len(rest_a), '->', len(rest_b), '; compared', int(match.sum()), 'outside the boxes;',
      int((keep & ~match).sum()), 'outside the boxes without a rest match (moved or new)')
for clip in MA.clips:
    if clip not in MB.clips:
        continue
    T = min(MA.clip_times(clip)[-1], MB.clip_times(clip)[-1])
    worst = (0.0, 0.0)
    for t in np.arange(0, T + 1e-9, 1.0 / o.fps):
        xa = np.concatenate([x for x, _ in MA.skinned_positions(MA.world(MA.sample(clip, t)))])
        xb = np.concatenate([x for x, _ in MB.skinned_positions(MB.world(MB.sample(clip, t)))])
        e = np.linalg.norm(xb[match] - xa[idx[match]], axis=1).max()
        if e > worst[0]:
            worst = (float(e), float(t))
    print(f'posed {clip}: max {worst[0] * 1000:.3f} mm at {worst[1]:.3f} s')
