#!/usr/bin/env python3
"""Magreeb gait: fore-aft travel of the four foot-tip joints over Walking and Running (stride = what a planted foot
sweeps per cycle; from mm9_lobber_claude/scripts/gait_measure.py). Usage: gait_measure.py <glb>"""
import sys
from pathlib import Path
import numpy as np
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'claude_shared' / 'floor'))
from glb_pose import Glb, Model
m = Model(Glb(sys.argv[1]))
names = [n.get('name') for n in m.glb.json['nodes']]
for clip in ('Walking', 'Running'):
    ts = np.linspace(0, m.clip_times(clip)[-1], 61)
    out = []
    for tip in ('Bone59', 'Bone64', 'Bone111', 'Bone117'):
        zs = np.array([np.asarray(m.world(m.sample(clip, t))[names.index(tip)])[2, 3] for t in ts])
        out.append(zs.max() - zs.min())
    print(clip, 'foot fore-aft travel', np.round(out, 3), 'mean %.3f' % np.mean(out))
