#!/usr/bin/env python3
"""Impact time of the club blow: the club head (the attachment's vertex farthest from its grip, on joint Club) per 1/120 s in the Attack;
impact = its fastest moment. Args: <body glb> <club glb>"""
import sys
from pathlib import Path
import numpy as np
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'claude_shared' / 'floor'))
from glb_pose import Glb, Model
g = Glb(Path(sys.argv[1])); m = Model(g); h = Glb(Path(sys.argv[2]))
P = h.accessor(h.json['meshes'][0]['primitives'][0]['attributes']['POSITION']).astype(float)
c = P.mean(0); tip = P[np.argmax(np.linalg.norm(P - c, axis=1))]
ci = [n.get('name') for n in g.json['nodes']].index('Club')
dur = m.clip_times('Attack')[-1]; T = np.arange(0, dur, 1 / 120)
X = np.array([(m.world(m.sample('Attack', float(t)))[ci] @ np.r_[tip, 1])[:3] for t in T])
v = np.linalg.norm(np.diff(X, axis=0), axis=1) * 120
k = int(np.argmax(v)); print('BLOW peak club-head speed', round(float(v[k]), 2), 'm/s at', round(float(T[k] + 1 / 240), 3), 's of', round(float(dur), 3))
