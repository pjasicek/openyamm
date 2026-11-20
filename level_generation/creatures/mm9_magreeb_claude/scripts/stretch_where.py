#!/usr/bin/env python3
"""Where do edges stretch? For each clip: the dominant joints of the vertices on edges whose posed/bind length ratio
exceeds a threshold (worst frame of a 30 Hz scan). Usage: stretch_where.py <glb> [threshold] [clips...]"""
import sys
from collections import Counter
from pathlib import Path
import numpy as np
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'claude_shared' / 'floor'))
from glb_pose import Glb, Model

m = Model(Glb(sys.argv[1]))
thr = float(sys.argv[2]) if len(sys.argv) > 2 else 2.5
doc = m.glb.json
names = {j: doc['nodes'][n].get('name') for j, n in enumerate(m.joints)}
clips = sys.argv[3:] or [a['name'] for a in doc['animations']]
rest = m.skinned_positions(m.world({}))
for clip in clips:
    times = m.clip_times(clip)
    worst = (0, None, None)
    for t in np.arange(times[0], times[-1] + 1e-6, 1 / 30):
        posed = m.skinned_positions(m.world(m.sample(clip, t)))
        cnt = Counter()
        n = 0
        for k, ((pos, tris), (rp, _)) in enumerate(zip(posed, rest)):
            e = np.unique(np.sort(np.concatenate([tris[:, [0, 1]], tris[:, [1, 2]], tris[:, [2, 0]]]), 1), axis=0)
            bl = np.linalg.norm(rp[e[:, 0]] - rp[e[:, 1]], axis=1)
            r = np.linalg.norm(pos[e[:, 0]] - pos[e[:, 1]], axis=1) / np.maximum(bl, 1e-6)
            bad = e[(r > thr) & (bl > 1e-4)]
            n += len(bad)
            pr = m.primitives[k]
            for a, b in bad:
                ja = names[int(pr['joints'][a][np.argmax(pr['weights'][a])])]
                jb = names[int(pr['joints'][b][np.argmax(pr['weights'][b])])]
                cnt[tuple(sorted((ja, jb)))] += 1
        if n > worst[0]:
            worst = (n, t, cnt)
    if worst[2]:
        print(clip, 'edges', worst[0], 't %.2f' % worst[1], worst[2].most_common(6))
    else:
        print(clip, 'none')
