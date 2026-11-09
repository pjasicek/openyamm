#!/usr/bin/env python3
"""The jitter gate's shoulder skin statistic is a 95th percentile over the vertices weighted mostly to the clavicle/upper arm, so
it changes when the reduction removes vertices even though every kept vertex moves exactly as installed. This prints, per side,
the gate's p95 and the max over vertices of the per-frame second difference (mm/f2, 48 fps), installed vs candidate, and the
same p95 on the installed file restricted to the candidate's vertices (by position). Usage: skin_acc_check.py <inst> <cand> <clip>"""
import sys
from pathlib import Path
import numpy as np
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'claude_shared' / 'floor'))
from glb_pose import Glb, Model
from scipy.spatial import cKDTree
def run(path, clip, restrict=None):
    g = Glb(path); m = Model(g); names = [n.get('name') for n in g.json['nodes']]; jn = [names[j] for j in m.joints]
    P = m.primitives; USE = [k for k, pr in enumerate(P) if pr['node'] == P[0]['node'] and pr['skinned']]
    dom = np.concatenate([np.array([jn[P[k]['joints'][v][np.argmax(P[k]['weights'][v])]] for v in range(len(P[k]['positions']))]) for k in USE])
    rest = np.concatenate([P[k]['positions'] for k in USE])
    ts = np.arange(0, max(m.clip_times(clip)) + 1e-6, 1 / 48)
    X = np.array([np.concatenate([sp[0] for k, sp in enumerate(m.skinned_positions(m.world(m.sample(clip, float(t))))) if k in USE]) for t in ts])
    out = {}
    for side, tok in (('L', ' L '), ('R', ' R ')):
        sv = np.where(np.isin(dom, [j for j in jn if tok in j and (j.endswith('Clavicle') or j.endswith('UpperArm'))]))[0]
        if restrict is not None:
            sv = sv[cKDTree(restrict).query(rest[sv])[0] < 1e-6]
        a = np.linalg.norm(X[2:, sv] - 2 * X[1:-1, sv] + X[:-2, sv], axis=2) * 1000
        out[side] = (len(sv), round(float(np.percentile(a, 95, axis=1).max()), 2), round(float(a.max()), 2))
    return out, rest
inst, cand, clip = sys.argv[1:4]
a, _ = run(inst, clip); b, rb = run(cand, clip); c, _ = run(inst, clip, rb)
print(clip, 'installed (verts, p95 max, vertex max)', a, '| candidate', b, '| installed on the candidate vertices', c)
