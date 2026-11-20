"""Rest-pose head points carried into a clip's pose at a time (forward kinematics of the GLB's nodes, the point
following one joint): where to aim review-viewer close-up cameras. Usage: posed_point.py <glb> <clip> <time> <joint>
x,y,z [x,y,z ...]"""
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
from glb import Glb  # noqa: E402


def quat(q):
    x, y, z, w = q
    return np.array([[1 - 2 * (y * y + z * z), 2 * (x * y - z * w), 2 * (x * z + y * w)],
                     [2 * (x * y + z * w), 1 - 2 * (x * x + z * z), 2 * (y * z - x * w)],
                     [2 * (x * z - y * w), 2 * (y * z + x * w), 1 - 2 * (x * x + y * y)]])


def trs(t, r, s):
    m = np.eye(4)
    m[:3, :3] = quat(r) * np.asarray(s)
    m[:3, 3] = t
    return m


g = Glb(sys.argv[1])
doc = g.doc
clip, time, joint = sys.argv[2], float(sys.argv[3]), sys.argv[4]
local = {i: [list(n.get('translation', [0, 0, 0])), list(n.get('rotation', [0, 0, 0, 1])), list(n.get('scale', [1, 1, 1]))]
         for i, n in enumerate(doc['nodes'])}
anim = next(a for a in doc['animations'] if a['name'] == clip)
for ch in anim['channels']:
    s = anim['samplers'][ch['sampler']]
    tin, out = g.accessor(s['input']), g.accessor(s['output'])
    k = int(np.clip(np.searchsorted(tin, time), 0, len(tin) - 1))
    path = ch['target']['path']
    local[ch['target']['node']][{'translation': 0, 'rotation': 1, 'scale': 2}[path]] = list(out[k])
parent = {c: i for i, n in enumerate(doc['nodes']) for c in n.get('children', [])}


def world(i):
    m = trs(*local[i])
    return world(parent[i]) @ m if i in parent else m


skin = doc['skins'][0]
j = next(i for i in skin['joints'] if doc['nodes'][i].get('name') == joint)
ibm = g.accessor(skin['inverseBindMatrices']).reshape(-1, 4, 4)[skin['joints'].index(j)].T
M = world(j) @ ibm
for a in sys.argv[5:]:
    p = np.array([float(v) for v in a.split(',')] + [1.0])
    print(a, '->', np.round((M @ p)[:3], 4).tolist())
