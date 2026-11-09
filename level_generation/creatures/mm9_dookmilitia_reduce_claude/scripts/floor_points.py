#!/usr/bin/env python3
"""Sole contact points of a LOD0 GLB for the LOD build (a first c378 build left LOD3 1.2 cm over the floor in Standing,
the installed LOD3 0.3 cm): rest-pose vertices of the limbs primitive within LOW m of the floor, in Blender's Z-up world
frame (glTF x, -z, y), deduplicated; plus the corpse contacts of Death/Dead (CLIPS). Usage: floor_points.py <lod0.glb> -> work/floor_points.json  (env LOW, default 0.004)"""
import json, os, sys
from pathlib import Path
import numpy as np
HERE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE.parent / 'claude_shared' / 'floor'))
from glb_pose import Glb, Model  # noqa: E402
LOW = float(os.environ.get('LOW', '0.004'))
m = Model(Glb(sys.argv[1]))
P = np.asarray(m.primitives[0]['positions'])
sel = P[P[:, 1] < P[:, 1].min() + LOW]
# the corpse: vertices (all primitives) within CORPSE_LOW (1.2 cm) of the lowest point at the lowest key of Death and Dead
# (c479: LOD2/3 of Dead dipped 6.7/7.7 mm under LOD0's lowest point, Death 9.3 at LOD3; the Phoenix lesson)
for clip in os.environ.get('CLIPS', 'Death,Dead').split(','):
    ts = m.clip_times(clip)
    t = min(ts, key=lambda t: min(float(np.asarray(pp[0])[:, 1].min()) for pp in m.skinned_positions(m.world(m.sample(clip, t)))))
    posed = m.skinned_positions(m.world(m.sample(clip, t)))
    low = min(float(np.asarray(pp[0])[:, 1].min()) for pp in posed)
    for k, pp in enumerate(posed):
        q = np.asarray(pp[0]); hit = q[:, 1] < low + float(os.environ.get('CORPSE_LOW', '0.012'))
        if hit.any():
            sel = np.vstack([sel, np.asarray(m.primitives[k]['positions'])[hit]])
pts = np.unique(np.round(sel[:, [0, 2, 1]] * [1, -1, 1], 6), axis=0)
(HERE / 'work' / 'floor_points.json').write_text(json.dumps(pts.tolist()))
print('FLOORPOINTS', len(pts), 'floor', round(float(P[:, 1].min()), 5))
