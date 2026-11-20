#!/usr/bin/env python3
"""Where the lining comes out (lining_gate.py follow-up): per clip frame the lining vertices more than TOL outside the posed skirt,
signed distance against ALL skirt faces (brute-force closest point), listed with rest position. Usage: lining_probe.py <glb> <clip> [tol m]"""
import sys
from pathlib import Path
import numpy as np
from scipy.spatial import cKDTree
HERE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE.parent / 'claude_shared' / 'floor')); sys.path.insert(0, str(HERE.parent / 'claude_shared'))
from glb_pose import Glb, Model  # noqa: E402
from detached_parts_audit import closest_on_triangles  # noqa: E402
glb, clip = sys.argv[1:3]; TOL = float(sys.argv[3]) if len(sys.argv) > 3 else 0.005
m = Model(Glb(glb)); body = m.primitives[0]
g = np.load(HERE / 'work' / 'glb_parts.npz'); fpart = g['part'][g['mat'] == 0]
src = Model(Glb(str(HERE / 'before' / 'mm9_peasantf8.glb'))).primitives[0]
vpart = np.full(len(src['positions']), -1); vpart[src['triangles'].ravel()] = np.repeat(fpart, 3)
P0, T0 = body['positions'], body['triangles']
_, j_ = cKDTree(src['positions']).query(P0); vp = vpart[j_]
part = vp[T0[:, 0]]
skirt = T0[part == 5]; linv = np.unique(T0[part == 9].ravel())
def signed(X):
    tr = X[skirt]; n = np.cross(tr[:, 1] - tr[:, 0], tr[:, 2] - tr[:, 0]); n /= np.maximum(np.linalg.norm(n, axis=1, keepdims=True), 1e-12)
    out = np.zeros(len(linv)); 
    for k, v in enumerate(linv):
        Q = np.repeat(X[v][None], len(tr), 0); q, _ = closest_on_triangles(Q, tr[:, 0], tr[:, 1], tr[:, 2])
        d = np.linalg.norm(q - Q, axis=1); i = d.argmin(); out[k] = ((X[v] - q[i]) * n[i]).sum()
    return out
rest = m.skinned_positions(m.world({}))[0][0]; s0 = signed(rest); sg = -1.0 if np.median(s0) > 0 else 1.0
t1 = m.clip_times(clip)[-1]; best = (0, None)
for t in np.append(np.arange(0, t1, 0.1), t1):
    X = m.skinned_positions(m.world(m.sample(clip, t)))[0][0]; sd = signed(X) * sg
    if sd.max() > best[0]:
        best = (sd.max(), t, sd.copy())
mx, t, sd = best
print(clip, 'worst', round(mx * 1000, 2), 'mm at', round(t, 2), 's')
for k in np.argsort(-sd)[:12]:
    if sd[k] < TOL: break
    v = linv[k]; print(f'  lining v{v} {sd[k]*1000:6.2f} mm rest {np.round(P0[v], 3)} rest signed {s0[k]*sg*1000:.2f}')
