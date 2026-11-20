#!/usr/bin/env python3
"""Jitter gate's shoulder-skin term (second difference at 30 fps of the vertices dominated by Clavicle/UpperArm, per side),
installed vs candidate: p95 per frame (the gate's statistic) and the max over vertices. The candidate's vertices are a subset
of the installed ones with identical skinning, so its max cannot exceed the installed max; a p95 rise is a sample-set change.
Usage: shoulder_subset.py <installed.glb> <candidate.glb> <clip,...>"""
import sys
from pathlib import Path
import numpy as np
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'claude_shared' / 'floor'))
from glb_pose import Glb, Model


def run(path, clip, tok):
    m = Model(Glb(path)); names = [n.get('name') for n in m.glb.json['nodes']]; jn = [names[j] for j in m.joints]
    P = [p for p in m.primitives if p['node'] == m.primitives[0]['node']]
    J = np.vstack([p['joints'] for p in P]); W = np.vstack([p['weights'] for p in P])
    fw = np.zeros((len(J), len(jn)))
    for c in range(J.shape[1]):
        np.add.at(fw, (np.arange(len(J)), J[:, c]), W[:, c])
    dom = np.array(jn)[fw.argmax(1)]
    sv = np.where(np.isin(dom, [j for j in jn if tok in j and (j.endswith('Clavicle') or j.endswith('UpperArm'))]))[0]
    ts = np.arange(0, max(m.clip_times(clip)) + 1e-6, 1 / 30)
    X = np.array([np.concatenate([sp[0] for sp in m.skinned_positions(m.world(m.sample(clip, float(t))))[:len(P)]]) for t in ts])[:, sv]
    a = np.linalg.norm(X[2:] - 2 * X[1:-1] + X[:-2], axis=2) * 1000
    return len(sv), np.percentile(a, 95, axis=1).max(), a.max()


for clip in sys.argv[3].split(','):
    for tok in (' L ', ' R '):
        r = [run(p, clip, tok) for p in sys.argv[1:3]]
        print(f'{clip:12s}{tok}: verts {r[0][0]} -> {r[1][0]}, p95 {r[0][1]:.2f} -> {r[1][1]:.2f} mm/f2, max {r[0][2]:.2f} -> {r[1][2]:.2f}')
