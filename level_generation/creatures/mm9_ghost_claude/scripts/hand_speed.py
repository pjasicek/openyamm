"""Which hand leads a clip at a time: hand speed and position. Args: glb clip t"""
import sys
from pathlib import Path
import numpy as np
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'claude_shared' / 'floor'))
from glb_pose import Glb, Model
m = Model(Glb(sys.argv[1])); c = sys.argv[2]; t = float(sys.argv[3])
names = {n.get('name'): i for i, n in enumerate(m.glb.json['nodes'])}
for n in ('Zhand', 'Zhand01'):
    a = m.world(m.sample(c, t - 0.03))[names[n]][:3, 3]; b = m.world(m.sample(c, t + 0.03))[names[n]][:3, 3]
    print(c, n, 'pos', np.round(b, 3), 'speed m/s', round(float(np.linalg.norm(b - a) / 0.06), 2))
