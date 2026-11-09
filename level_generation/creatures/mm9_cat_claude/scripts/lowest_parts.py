#!/usr/bin/env python3
"""Per clip: the lowest point and the joint that dominates it (find what sinks). Usage: lowest_parts.py <glb> [clip ...]"""
import sys
from pathlib import Path
import numpy as np
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'claude_shared' / 'floor'))
from glb_pose import Glb, Model
m = Model(Glb(sys.argv[1]))
doc = m.glb.json
names = [n.get('name') for n in doc['nodes']]
clips = sys.argv[2:] or [a['name'] for a in doc['animations']]
prim = m.primitives[0]
J = prim['joints'][np.arange(len(prim['joints'])), prim['weights'].argmax(1)]
for clip in clips:
    ts = m.clip_times(clip)
    ts = np.arange(ts[0], ts[-1] + 1e-6, 1 / 30)
    best = (1e9, 0, 0)
    for t in ts:
        pos, _ = m.skinned_positions(m.world(m.sample(clip, t)))[0]
        i = int(pos[:, 1].argmin())
        if pos[i, 1] < best[0]:
            best = (float(pos[i, 1]), float(t), i)
    y, t, i = best
    pos, _ = m.skinned_positions(m.world(m.sample(clip, t)))[0]
    lowset = np.nonzero(pos[:, 1] < y + 0.05)[0]
    from collections import Counter
    jn = Counter(names[m.joints[int(j)]] for j in J[lowset]).most_common(3)
    print(f'{clip:13s} low {y:+.3f} at t {t:.2f}, {len(lowset)} verts within 5 cm: {jn}')
