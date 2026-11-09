#!/usr/bin/env python3
"""Walk/run strides from the foot travel: fore-aft range of each foot joint (relative to the body) over the clip;
stride (body advance per cycle) = range / stance duty (walk 0.6, run 0.4). Usage: stride.py <glb> <foot joints>"""
import sys
from pathlib import Path
import numpy as np
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'claude_shared' / 'floor'))
from glb_pose import Glb, Model
m = Model(Glb(sys.argv[1]))
names = [n.get('name') for n in m.glb.json['nodes']]
for clip, duty in (('Walking', 0.6), ('Running', 0.4)):
    if clip not in m.clips:
        continue
    ts = np.linspace(0, m.clip_times(clip)[-1], 61)
    rng = []
    for foot in sys.argv[2].split(','):
        z = np.array([np.asarray(m.world(m.sample(clip, t))[names.index(foot)])[2, 3] for t in ts])
        rng.append(z.max() - z.min())
    L = float(np.mean(rng))
    print(f'{clip}: foot fore-aft range {L:.3f} (per foot {np.round(rng, 3)}), stride {L / duty:.3f} model units')
