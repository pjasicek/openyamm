#!/usr/bin/env python3
"""Per clip: the lowest vertex over the keys, its time and its dominant joint. Usage: lowest_joint.py <glb> [clips]"""
import sys
from pathlib import Path
import numpy as np
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'claude_shared' / 'floor'))
from glb_pose import Glb, Model
m = Model(Glb(sys.argv[1]))
nodes = m.glb.json['nodes']
clips = sys.argv[2].split(',') if len(sys.argv) > 2 else list(m.clips)
for clip in clips:
    best = (1e9, 0, None)
    for t in m.clip_times(clip):
        posed = m.skinned_positions(m.world(m.sample(clip, t)))
        for (pts, _), prim in zip(posed, m.primitives):
            i = int(np.argmin(pts[:, 1]))
            if pts[i, 1] < best[0]:
                j = prim['joints'][i][int(np.argmax(prim['weights'][i]))] if prim['skinned'] else -1
                best = (pts[i, 1], t, nodes[m.joints[j]]['name'] if j >= 0 else '-')
    print(f'{clip:13s} lowest {best[0]:+.4f} at {best[1]:.2f} s joint {best[2]}')
