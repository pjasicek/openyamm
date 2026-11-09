#!/usr/bin/env python3
"""One posed point against the body cloth (glb_parts dress + skirt faces, matched to the GLB's own faces by vertex position):
nearest face distance and signed side, ray hit counts in 6 axis directions (parity: odd = inside a closed cloth tube).
Usage: point_probe.py <glb> <clip> <t s> <x,y,z>"""
import sys
from pathlib import Path
import numpy as np
from scipy.spatial import cKDTree
HERE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE.parent / 'claude_shared' / 'floor')); sys.path.insert(0, str(HERE.parent / 'claude_shared'))
from glb_pose import Glb, Model  # noqa: E402
from detached_parts_audit import closest_on_triangles  # noqa: E402
glb, clip, t, xyz = sys.argv[1:5]; pt = np.array([float(v) for v in xyz.split(',')])
src = Model(Glb(str(HERE / 'before' / 'mm9_peasantf5.glb'))).primitives[0]
g = np.load(HERE / 'work' / 'glb_parts.npz'); fpart = g['part'][g['mat'] == 0]
vpart = np.full(len(src['positions']), -1); vpart[src['triangles'].ravel()] = np.repeat(fpart, 3)
m = Model(Glb(glb)); body = m.primitives[0]
_, j = cKDTree(src['positions']).query(body['positions']); part = vpart[j][body['triangles'][:, 0]]
X = m.skinned_positions(m.world(m.sample(clip, float(t))))[0][0]; PARTS = tuple(int(x) for x in __import__('os').environ.get('PARTS', '1,2').split(',')); F = body['triangles'][np.isin(part, PARTS)]; FP = part[np.isin(part, PARTS)]
a, b, c = X[F[:, 0]], X[F[:, 1]], X[F[:, 2]]
q, _ = closest_on_triangles(np.repeat(pt[None], len(F), 0), a, b, c); d = np.linalg.norm(q - pt, axis=1); k = d.argmin()
n = np.cross(b - a, c - a); n /= np.maximum(np.linalg.norm(n, axis=1, keepdims=True), 1e-12)
print('nearest cloth face part', int(FP[k]), round(float(d[k]) * 100, 2), 'cm, side', round(float((pt - q[k]) @ n[k]) * 100, 2), 'cm')
for dv in np.r_[np.eye(3), -np.eye(3)]:
    e1, e2 = b - a, c - a; pv = np.cross(dv, e2); det = (e1 * pv).sum(1); ok = np.abs(det) > 1e-12
    inv = np.where(ok, 1 / np.where(ok, det, 1), 0); tv = pt - a; u = (tv * pv).sum(1) * inv; qv = np.cross(tv, e1)
    v = (qv @ dv) * inv; tt = (e2 * qv).sum(1) * inv; hit = ok & (u >= 0) & (v >= 0) & (u + v <= 1) & (tt > 0)
    print('  ray', dv.astype(int).tolist(), 'hits', int(hit.sum()), 'first cm', np.round(np.sort(tt[hit])[:3] * 100, 1).tolist())
