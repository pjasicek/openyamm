#!/usr/bin/env python3
"""Gait: fore-aft travel of the given foot joints over Walking and Running (stride = what a planted foot sweeps per
cycle; from ../mm9_lobber_claude/scripts/gait_measure.py). Usage: gait_measure.py <glb> <joint> [...]"""
import sys
from pathlib import Path
import numpy as np
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'claude_shared' / 'floor'))
from glb_pose import Glb, Model
m = Model(Glb(sys.argv[1]))
names = [n.get('name') for n in m.glb.json['nodes']]
for clip in ('Walking', 'Running'):
    ts = np.linspace(0, m.clip_times(clip)[-1], 61)
    for tip in sys.argv[2:]:
        zs = np.array([np.asarray(m.world(m.sample(clip, t))[names.index(tip)])[2, 3] for t in ts])  # glTF z = fwd
        print(clip, tip, 'fore-aft travel %.3f' % (zs.max() - zs.min()))
