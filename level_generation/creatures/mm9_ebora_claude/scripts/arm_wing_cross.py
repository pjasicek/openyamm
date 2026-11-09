#!/usr/bin/env python3
"""Arm through wing: per clip frame, count forearm/hand mesh edges that cross a wing membrane triangle (segment against
triangle, Moller-Trumbore), and the deepest forearm vertex below the membrane it lies over (distance along the membrane
normal, within 6 cm). Args: <glb> <clip,...> [fps]"""
import sys
from pathlib import Path
import numpy as np
from scipy.spatial import cKDTree
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'claude_shared' / 'floor'))
from glb_pose import Glb, Model
m = Model(Glb(sys.argv[1])); doc = m.glb.json; mats = [x['name'] for x in doc['materials']]
clips = sys.argv[2].split(','); fps = float(sys.argv[3]) if len(sys.argv) > 3 else 24
jn = [doc['nodes'][j]['name'] for j in m.joints]
prims = [i for i, p in enumerate(m.primitives) if m.primitives[i]['node'] == m.primitives[0]['node']]
mat_of = [doc['meshes'][0]['primitives'][i]['material'] for i in range(len(doc['meshes'][0]['primitives']))]
wing = [i for i in range(len(mat_of)) if mats[mat_of[i]].startswith('EboraWing')][0]
torso = [i for i in range(len(mat_of)) if mats[mat_of[i]].startswith('EboraTorso')][0]
pr = m.primitives[torso]; dom = np.array([jn[pr['joints'][v][np.argmax(pr['weights'][v])]] for v in range(len(pr['positions']))])
wp = m.primitives[wing]; wdom = np.array([jn[wp['joints'][v][np.argmax(wp['weights'][v])]] for v in range(len(wp['positions']))])
WT = wp['triangles']
for side in ('L', 'R'):
    arm = np.isin(dom, [j for j in jn if f' {side} ' in j and any(k in j for k in ('Forearm', 'Hand', 'Thumb', 'Index', 'Middle', 'Ring', 'Pinky'))])
    T = pr['triangles']; at = T[arm[T].all(1)]
    E = np.unique(np.sort(np.vstack([at[:, [0, 1]], at[:, [1, 2]], at[:, [2, 0]]]), 1), axis=0)
    for c in clips:
        dur = m.clip_times(c)[-1]; worst = (0, 0, 0)
        for t in np.arange(0, dur + 1e-6, 1 / fps):
            posed = m.skinned_positions(m.world(m.sample(c, float(t))))
            P = posed[torso][0]; Q = posed[wing][0]
            a, b = P[E[:, 0]], P[E[:, 1]]
            v0, v1, v2 = Q[WT[:, 0]], Q[WT[:, 1]], Q[WT[:, 2]]
            lo = np.minimum(np.minimum(v0, v1), v2).min(0); hi = np.maximum(np.maximum(v0, v1), v2).max(0)
            sel = ((np.minimum(a, b) <= hi) & (np.maximum(a, b) >= lo)).all(1)
            n = 0
            if sel.any():
                kd = cKDTree((v0 + v1 + v2) / 3)
                for ea, eb in zip(a[sel], b[sel]):
                    cand = kd.query_ball_point((ea + eb) / 2, 0.08)
                    if not cand: continue
                    d = eb - ea; e1 = v1[cand] - v0[cand]; e2 = v2[cand] - v0[cand]
                    pv = np.cross(d, e2); det = (e1 * pv).sum(1); ok = np.abs(det) > 1e-12
                    inv = np.where(ok, 1 / np.where(ok, det, 1), 0); tv = ea - v0[cand]
                    u = (tv * pv).sum(1) * inv; qv = np.cross(tv, e1); w = (d * qv).sum(1) * inv; s = (e2 * qv).sum(1) * inv
                    if (ok & (u >= 0) & (w >= 0) & (u + w <= 1) & (s >= 0) & (s <= 1)).any(): n += 1
            if n > worst[0]: worst = (n, round(t, 2), 0)
        print(f'{c:8s} {side}: arm edges through the wing, worst frame {worst[0]} at {worst[1]} s')
