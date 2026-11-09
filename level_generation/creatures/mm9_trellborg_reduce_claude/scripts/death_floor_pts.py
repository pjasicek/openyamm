#!/usr/bin/env python3
"""Floor-contact vertices of the dying clips on a LOD0 GLB (glb_pose skinning at 30 fps; within NEAR m of the frame's lowest point in
Death, Death2, Dead), written as Blender rest coordinates (x, -z, y) for build_lods.py's protected points (MM8 batch lesson: LOD2's
corpse went 1 cm under the floor in Death2). Usage: death_floor_pts.py <lod0.glb> <out.npy>"""
import os, sys
from pathlib import Path
import numpy as np
HERE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE.parent / 'claude_shared' / 'floor'))
from glb_pose import Glb, Model
NEAR = float(os.environ.get('NEAR', .006))
m = Model(Glb(Path(sys.argv[1])))
P = [p for p in m.primitives if p['node'] == m.primitives[0]['node'] and p['skinned']]
X0 = np.vstack([p['positions'] for p in P]); low = np.zeros(len(X0), bool)
for clip in ('Death', 'Death2', 'Dead'):
    for t in np.arange(0, max(m.clip_times(clip)) + 1e-6, 1 / 30):
        Y = np.vstack([sp[0] for k, sp in enumerate(m.skinned_positions(m.world(m.sample(clip, float(t))))) if k < len(P)])
        low |= Y[:, 1] < Y[:, 1].min() + NEAR
B = X0[low][:, [0, 2, 1]] * [1, -1, 1]
np.save(sys.argv[2], B); print('DEATHFLOOR', int(low.sum()), 'vertices')
