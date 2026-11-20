"""Jaw opening per clip: angle of the Xjaw->XjawA line against the head's Xhead->XheadB line, minus the bind value
(positive = wider than bind). Args: glb"""
import sys
from pathlib import Path
import numpy as np
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'claude_shared' / 'floor'))
from glb_pose import Glb, Model
m = Model(Glb(sys.argv[1])); doc = m.glb.json; ix = {n.get('name'): i for i, n in enumerate(doc['nodes'])}
def ang(w):
    h = w[ix['XheadB']][:3, 3] - w[ix['Xhead']][:3, 3]; j = w[ix['XjawA']][:3, 3] - w[ix['Xjaw']][:3, 3]
    return np.degrees(np.arccos(np.clip(h @ j / np.linalg.norm(h) / np.linalg.norm(j), -1, 1)))
b = ang(m.world({}))
for a in doc['animations']:
    T = m.clip_times(a['name'])[-1]; v = [ang(m.world(m.sample(a['name'], t))) - b for t in np.arange(0, T + 1e-6, 1 / 30)]
    print(f"{a['name']:13s} min {min(v):6.1f} max {max(v):6.1f}")
print('bind gape', round(b, 1))
