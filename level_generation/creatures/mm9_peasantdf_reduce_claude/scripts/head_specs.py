#!/usr/bin/env python3
"""Viewer specs framed on the face: the target is a point fixed in the head bone (face centre, found in Standing 0.5 at the
head joint + UP), the camera at target + dir * dist (world). Usage: head_specs.py <glb> <prefix> <clip:seconds> <dx,dy,dz:dist> ..."""
import sys
from pathlib import Path
import numpy as np
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'claude_shared' / 'floor'))  # copied from mm9_ebora_claude
from glb_pose import Glb, Model
import os
UP = np.array([float(v) for v in os.environ.get("HEADUP", "0.0,0.10,0.06").split(",")])
glb, pre, cs = sys.argv[1:4]; m = Model(Glb(glb)); names = [n.get('name') for n in m.glb.json['nodes']]; h = names.index(os.environ.get('HEADBONE', 'FHP Head'))
w0 = m.world(m.sample('Standing', 0.5))[h]; loc = np.linalg.inv(w0) @ np.r_[w0[:3, 3] + UP, 1]
clip, sec = cs.split(':'); w = m.world(m.sample(clip, float(sec)))[h]; p = (w @ loc)[:3]
for k, it in enumerate(sys.argv[4:]):
    o, d = it.split(':'); o = np.array([float(x) for x in o.split(',')]); o = o / np.linalg.norm(o) * float(d)
    print(f'{pre}{k}:{clip}:{sec}:front:body:' + ','.join(f'{x:.3f}' for x in p + o) + ':' + ','.join(f'{x:.3f}' for x in p))
