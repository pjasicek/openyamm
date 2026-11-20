#!/usr/bin/env python3
"""Hand faces (labels.npz reg 2) by the posed MPFB finger chains of ../mm9_trellborg_claude/work/fist.json (4 points per finger: knuckle,
two joints, tip; same frame as the source): nearest segment within FR m -> 1 proximal, 2 middle, 3 distal phalanx; else 0 palm/back.
Adds 'hseg' to work/labels.npz; also 'grip': hand faces within GRIPD of the club at rest."""
import json, os
from pathlib import Path
import numpy as np
from scipy.spatial import cKDTree
HERE = Path(__file__).resolve().parents[1]
d = np.load(HERE / 'work/mesh_in.npz'); L = dict(np.load(HERE / 'work/labels.npz')); V, F = d['verts'], d['faces']
fc = V[F].mean(1); hand = L['reg'] == 2
J = json.load(open(HERE.parent / 'mm9_trellborg_claude/work/fist.json'))
FR = float(os.environ.get('FR', .03)); GRIPD = float(os.environ.get('GRIPD', .015))
best = np.full(len(F), np.inf); seg = np.zeros(len(F), int)
for S in 'RL':
    for name, pts in J[S]['posed'].items():
        pts = np.array(pts)
        for s in range(3):
            a, b = pts[s], pts[s + 1]; ab = b - a
            t = np.clip(((fc - a) @ ab) / (ab @ ab), 0, 1); dd = np.linalg.norm(fc - (a + t[:, None] * ab), axis=1)
            m = dd < best; best[m] = dd[m]; seg[m] = s + 1
hseg = np.where(hand & (best < FR), seg, 0)
club = np.unique(F[L['reg'] == 8]); grip = hand & (cKDTree(V[club]).query(fc)[0] < GRIPD)
L['hseg'] = hseg; L['grip'] = grip
print('hand', int(hand.sum()), {k: int(((hseg == k) & hand).sum()) for k in range(4)}, 'grip', int(grip.sum()), 'distance p50/p90', np.percentile(best[hand], [50, 90]).round(3))
np.savez(HERE / 'work/labels.npz', **L)
