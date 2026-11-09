#!/usr/bin/env python3
"""Hand acceleration percentiles, final clips against the raw (unthinned) MM9 keys. Args: <final glb> <raw glb>"""
import sys
from pathlib import Path
import numpy as np
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'claude_shared' / 'floor'))
from glb_pose import Glb, Model
A, B = [Model(Glb(p)) for p in sys.argv[1:3]]
for clip in ('Standing', 'Walking', 'Running', 'Fidget', 'AttackMelee', 'AttackRanged', 'Hit'):
    out = []
    for m in (A, B):
        n = [x.get('name') for x in m.glb.json['nodes']]
        T = np.arange(0, m.clip_times(clip)[-1], 1 / 48)
        v = []
        for j in ('Bip01 L Hand', 'Bip01 R Hand'):
            i = n.index(j); P = np.array([m.world(m.sample(clip, float(t)))[i][:3, 3] for t in T])
            v.append(np.linalg.norm(np.diff(P, 2, axis=0), axis=1) * 1000)
        v = np.concatenate(v); out.append((np.percentile(v, 50), np.percentile(v, 95), v.max()))
    print(f'{clip:13s} final p50/p95/max {out[0][0]:.1f} {out[0][1]:.1f} {out[0][2]:.1f}   raw {out[1][0]:.1f} {out[1][1]:.1f} {out[1][2]:.1f}')
