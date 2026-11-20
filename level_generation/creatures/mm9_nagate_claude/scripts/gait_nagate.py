#!/usr/bin/env python3
"""Nagate gait: fore-aft travel of the six toe joints over one Walking / Running cycle (a planted foot sweeps the
stride per cycle). Usage: gait_nagate.py <glb>"""
import sys
from pathlib import Path
import numpy as np
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'claude_shared' / 'floor'))
from glb_pose import Glb, Model
m = Model(Glb(sys.argv[1]))
names = [n.get('name') for n in m.glb.json['nodes']]
TOES = ('Xatoe', 'Xatoe02', 'Xbtoe', 'Xbtoe05', 'Xbtoe01', 'Xbtoe04')
for clip in ('Walking', 'Running'):
    ts = np.linspace(0, m.clip_times(clip)[-1], 61)
    travel = []
    for tip in TOES:
        zs = np.array([np.asarray(m.world(m.sample(clip, t))[names.index(tip)])[2, 3] for t in ts])
        travel.append(zs.max() - zs.min())
    print(clip, 'duration %.3f' % m.clip_times(clip)[-1], 'toe fore-aft travel', ' '.join('%.3f' % x for x in travel),
          'median %.3f' % float(np.median(travel)))
