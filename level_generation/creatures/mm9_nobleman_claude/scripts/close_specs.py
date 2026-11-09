#!/usr/bin/env python3
"""Viewer close-up shot specs around joints. Usage: close_specs.py <glb> <prefix> <clip:seconds> <joint:ox,oy,oz:dist> ..."""
import sys
from pathlib import Path
import numpy as np
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'claude_shared' / 'floor'))
from glb_pose import Glb, Model
glb, pre, cs = sys.argv[1:4]; m = Model(Glb(glb)); names = [n.get('name') for n in m.glb.json['nodes']]
clip, sec = cs.split(':'); w = m.world(m.sample(clip, float(sec)))
import os
w0 = m.world({}); ref = names.index(os.environ.get('REF', 'Bip01 Spine2'))
R = w[ref][:3, :3] @ np.linalg.inv(w0[ref][:3, :3])     # offsets are in the body's rest frame, so a lying corpse is framed from the same body side
R = np.linalg.svd(R)[0] @ np.linalg.svd(R)[2]
for k, it in enumerate(sys.argv[4:]):
    j, o, d = it.split(':'); p = w[names.index(j)][:3, 3]
    o = np.array([float(x) for x in o.split(',')]); o = R @ (o / np.linalg.norm(o) * float(d))
    print(f'{pre}{k}:{clip}:{sec}:front:body:' + ','.join(f'{x:.3f}' for x in p + o) + ':' + ','.join(f'{x:.3f}' for x in p))
