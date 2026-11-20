#!/usr/bin/env python3
"""Held props against the body, per clip (humanoid playbook G6: nothing inside the skin/cloth). The staff (head-set vertices rigid on
FHP R Hand) and the held skull (rigid on FHP L Hand) are tested against the outer cloth (body-set vertices off the hands, whose rest normal
points away from the body's vertical axis: the inner linings are left out), signed distance along the nearest outer vertex's posed normal;
a prop vertex more than TOL behind the cloth and within 6 cm of it counts. 24 fps. Args: <glb> <out json> [tol 0.01]"""
import json, sys
from pathlib import Path
import numpy as np
from scipy.spatial import cKDTree
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'claude_shared' / 'floor'))
from glb_pose import Glb, Model
glb, out = sys.argv[1:3]; TOL = float(sys.argv[3]) if len(sys.argv) > 3 else 0.01
m = Model(Glb(glb)); doc = m.glb.json; nn = [n.get('name') for n in doc['nodes']]
jn = [nn[j] for j in m.joints]
mats = [doc['materials'][p['material']]['name'] for p in doc['meshes'][[n.get('mesh') for n in doc['nodes'] if 'mesh' in n][0]]['primitives']]
prims = m.primitives[:len(mats)]
def rigid_on(pr, name):
    j = jn.index(name); return (pr['joints'][:, 0] == j) & (pr['weights'][:, 0] > 0.99)
bi = mats.index('Skraelos'); hi = mats.index('SkraelosHead')
body, head = prims[bi], prims[hi]
handj = [i for i, n in enumerate(jn) if any(k in n for k in ('Hand', 'Finger', 'Thumb', 'Index', 'Middle', 'Ring', 'Pinky'))]
offhand = ~np.isin(body['joints'][:, 0], handj)
P0 = body['positions']; T0 = body['triangles']
fn = np.cross(P0[T0[:, 1]] - P0[T0[:, 0]], P0[T0[:, 2]] - P0[T0[:, 0]]); N0 = np.zeros_like(P0)
for c in range(3): np.add.at(N0, T0[:, c], fn)
N0 /= np.maximum(np.linalg.norm(N0, axis=1, keepdims=True), 1e-12)
radial = P0.copy(); radial[:, 1] = 0; outer = offhand & (np.sum(N0 * radial, 1) > 0)
props = {'staff': rigid_on(head, 'FHP R Staff' if 'FHP R Staff' in jn else 'FHP R Hand'), 'skull': rigid_on(head, 'FHP L Hand')}
res = {}
for clip in m.clips:
    times = m.clip_times(clip); t = np.arange(0, times[-1] + 1e-6, 1 / 24.0)
    r = {k: {'frames': 0, 'max_cm': 0.0} for k in props}
    for tt in t:
        w = m.world(m.sample(clip, tt)); posed = m.skinned_positions(w)
        Pb = posed[bi][0]; Ph = posed[hi][0]
        fnp = np.cross(Pb[T0[:, 1]] - Pb[T0[:, 0]], Pb[T0[:, 2]] - Pb[T0[:, 0]]); Nb = np.zeros_like(Pb)
        for c in range(3): np.add.at(Nb, T0[:, c], fnp)
        Nb /= np.maximum(np.linalg.norm(Nb, axis=1, keepdims=True), 1e-12)
        oi = np.where(outer)[0]; kd = cKDTree(Pb[oi])
        for k, msk in props.items():
            q = Ph[msk]; d, i = kd.query(q); s = np.sum((q - Pb[oi[i]]) * Nb[oi[i]], 1)
            bad = (s < -TOL) & (d < 0.06)
            if bad.any():
                r[k]['frames'] += 1; r[k]['max_cm'] = max(r[k]['max_cm'], round(float(-s[bad].min()) * 100, 1))
                c_ = q.mean(0); u_ = np.linalg.svd(q - c_)[2][0]; tt_ = (q - c_) @ u_; L_ = max(np.abs(tt_).max(), 1e-6)
                if u_[1] < 0: tt_ = -tt_          # + = the upper end (glTF y up)
                r[k].setdefault('where', []).append(round(float(np.median(tt_[bad]) / L_), 2)); r[k].setdefault('t', []).append(round(float(tt), 2))
    for k in r:
        r[k]['of'] = len(t)
        if 'where' in r[k]: w_ = r[k].pop('where'); r[k]['along_p10_p50_p90'] = np.percentile(w_, [10, 50, 90]).round(2).tolist()
    res[clip] = r; print(clip, r)
json.dump(res, open(out, 'w'), indent=1)
