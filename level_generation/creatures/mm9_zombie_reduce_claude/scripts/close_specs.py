#!/usr/bin/env python3
"""Close viewer specs aimed at a joint (posed world position + offset): name:clip:sec:joint:dx,dy,dz:dist[:ox,oy,oz].
Usage: close_specs.py <glb> <spec> ...  -> viewer_shots.mjs specs (camera and target in glTF metres)"""
import sys
from pathlib import Path
import numpy as np
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'claude_shared' / 'floor'))
from glb_pose import Glb, Model
m = Model(Glb(sys.argv[1])); names = [n.get('name') for n in m.glb.json['nodes']]
for it in sys.argv[2:]:
    f = it.split(':'); name, clip, sec, joint, d, dist = f[:6]
    off = np.array([float(x) for x in f[6].split(',')]) if len(f) > 6 else np.zeros(3)
    p = m.world(m.sample(clip, float(sec)))[names.index(joint)][:3, 3] + off
    d = np.array([float(x) for x in d.split(',')]); d = d / np.linalg.norm(d) * float(dist)
    print(f'{name}:{clip}:{sec}:front:body:' + ','.join(f'{x:.3f}' for x in p + d) + ':' + ','.join(f'{x:.3f}' for x in p))
