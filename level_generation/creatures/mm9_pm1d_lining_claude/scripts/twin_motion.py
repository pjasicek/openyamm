#!/usr/bin/env python3
"""Lining twins move with the cloth they line: for every band twin (line.py role 'twin') the per-frame second difference
(mm/frame^2 at 30 fps) against its source vertex (the original vertex with the same joints and weights nearest at rest), every
clip; and the p95 of the shoulder sample with and without the new vertices (jitter_gate.py's 'shoulder skin': vertices weighted
mostly to a side's Clavicle or UpperArm). Usage: twin_motion.py <lined glb> <lining npz> [clips]"""
import sys
from pathlib import Path
import numpy as np
from scipy.spatial import cKDTree
HERE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE.parent / 'claude_shared' / 'floor'))
from glb_pose import Glb, Model  # noqa: E402
m = Model(Glb(sys.argv[1])); z = np.load(sys.argv[2]); clips = sys.argv[3].split(',') if len(sys.argv) > 3 else m.clips
pr = m.primitives[0]; n0 = int(z['nvert_PM1d_C']); tags = z['vtag_PM1d_C']
tw = np.array([n0 + i for i, t in enumerate(tags) if t.split('|')[1] == 'twin'])
P, J, W = pr['positions'], pr['joints'], pr['weights']
src = np.zeros(len(tw), int)
key = {}
for i in range(n0):
    key.setdefault((tuple(J[i]), tuple(np.round(W[i], 6))), []).append(i)
for k, v in enumerate(tw):
    c = key[(tuple(J[v]), tuple(np.round(W[v], 6)))]; src[k] = c[int(np.argmin(np.linalg.norm(P[c] - P[v], axis=1)))]
doc = m.glb.json; skin = doc['skins'][0]; jn = [doc['nodes'][j]['name'] for j in skin['joints']]
dom = np.array([jn[J[i][np.argmax(W[i])]] for i in range(len(P))])
for clip in clips:
    t1 = m.clip_times(clip)[-1]; ts = np.arange(0, t1 + 1e-9, 1 / 30)
    X = np.array([m.skinned_positions(m.world(m.sample(clip, float(t))))[0][0] for t in ts])
    A = np.linalg.norm(X[2:] - 2 * X[1:-1] + X[:-2], axis=2) * 1000
    d = np.abs(A[:, tw] - A[:, src]).max()
    line = f'{clip:12s} twin vs source acc max diff {d:.3f} mm/f2'
    for side in (' L ', ' R '):
        sv = np.array([i for i in range(len(P)) if side in dom[i] and (dom[i].endswith('Clavicle') or dom[i].endswith('UpperArm'))])
        so = sv[sv < n0]
        line += f' |{side.strip()} shoulder p95 max: original verts {np.percentile(A[:, so], 95, axis=1).max():.2f}, with linings {np.percentile(A[:, sv], 95, axis=1).max():.2f}'
    print(line, flush=True)
