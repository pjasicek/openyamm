"""World positions (viewer glTF frame, Y up) of named joints at clip:time. usage: joint_pos.py <glb> <clip:t> <joint> ..."""
import sys
from pathlib import Path
import numpy as np
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'claude_shared' / 'floor'))
from glb_pose import Glb, Model
m = Model(Glb(sys.argv[1])); names = [n.get('name') for n in m.glb.json['nodes']]
c, t = sys.argv[2].split(':'); W = m.world(m.sample(c, float(t)))
for j in sys.argv[3:]:
    print(j, np.round(W[names.index(j)][:3, 3], 3).tolist())
