"""Front-on head cameras riding the head joint. Args: <glb> <prefix> clip:t ..."""
import sys
from pathlib import Path
import numpy as np
sys.path.insert(0, '../claude_shared/floor')
from glb_pose import Glb, Model
m = Model(Glb(Path(sys.argv[1]))); nm = [n.get('name') for n in m.glb.json['nodes']]; i = nm.index('Bip01 Head')
w0 = m.world({})[i]
for k, cs in enumerate(sys.argv[3:]):
    c, t = cs.split(':'); w = m.world(m.sample(c, float(t)))[i]; R = w[:3, :3] @ np.linalg.inv(w0[:3, :3])
    p = w[:3, 3] + R @ np.array([0, 0.12, 0.12]); f = R @ np.array([0, 0, 1.0]); cam = p + f * 0.95
    print(f'{sys.argv[2]}{k}:{c}:{t}:front:body:' + ','.join(f'{x:.3f}' for x in cam) + ':' + ','.join(f'{x:.3f}' for x in p))
