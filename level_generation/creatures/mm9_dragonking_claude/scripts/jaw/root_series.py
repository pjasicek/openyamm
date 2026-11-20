#!/usr/bin/env python3
"""Per clip and key: the Xhead joint height, the lowest visible point and the root joint height of one or more GLBs
(same rig), to compare floor passes. Usage: root_series.py <out.json> <label=glb>... [--clips A,B]"""
import sys, json
from pathlib import Path
import numpy as np
sys.path.insert(0, str(Path(__file__).resolve().parents[3] / 'claude_shared/floor'))
import glb_pose
args = sys.argv[1:]
out = args[0]; clips = None
if '--clips' in args:
    clips = args[args.index('--clips') + 1].split(','); args = args[:args.index('--clips')]
res = {}
for spec in args[1:]:
    label, path = spec.split('=', 1)
    m = glb_pose.Model(glb_pose.Glb(path))
    names = {n.get('name'): i for i, n in enumerate(m.glb.json['nodes'])}
    head = names['Xhead']; root = m.root_joints[0]
    res[label] = {}
    for clip in (clips or list(m.clips)):
        rows = []
        for t in m.clip_times(clip):
            local = m.sample(clip, t); w = m.world(local)
            rows.append([round(float(t), 4), float(w[head][1, 3]), float(w[root][1, 3]), float(m.lowest(clip, t) or 0)])
        res[label][clip] = rows
        a = np.array(rows)
        print(f'{label:8s} {clip:12s} keys {len(a):3d} head {a[:,1].min():7.3f}..{a[:,1].max():7.3f} (range {np.ptp(a[:,1]):.3f}) '
              f'root {a[:,2].min():7.3f}..{a[:,2].max():7.3f} (range {np.ptp(a[:,2]):.3f}) lowest {a[:,3].min():+.3f}..{a[:,3].max():+.3f}')
json.dump(res, open(out, 'w'))
