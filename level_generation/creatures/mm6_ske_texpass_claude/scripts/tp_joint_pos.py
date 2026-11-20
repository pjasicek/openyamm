"""World position (glTF, metres) of a node at a clip time (first key at or before it, no interpolation), for free
review cameras. Usage: tp_joint_pos.py <glb> <clip> <seconds> <node name>[,<node name>...]"""
import sys

import numpy as np

from glb import Glb

g = Glb(sys.argv[1])
doc = g.doc
clip = next(a for a in doc['animations'] if a['name'] == sys.argv[2])
t = float(sys.argv[3])
local = {}
for i, n in enumerate(doc['nodes']):
    local[i] = {'translation': np.array(n.get('translation', [0, 0, 0]), float),
                'rotation': np.array(n.get('rotation', [0, 0, 0, 1]), float),
                'scale': np.array(n.get('scale', [1, 1, 1]), float)}
for ch in clip['channels']:
    s = clip['samplers'][ch['sampler']]
    times = g.accessor(s['input'])
    values = g.accessor(s['output'])
    k = max(int(np.searchsorted(times, t, side='right')) - 1, 0)
    if ch['target']['path'] in local[ch['target']['node']]:
        local[ch['target']['node']][ch['target']['path']] = values[k].astype(float)


def matrix(n):
    x, y, z, w = local[n]['rotation']
    r = np.array([[1 - 2 * (y * y + z * z), 2 * (x * y - z * w), 2 * (x * z + y * w)],
                  [2 * (x * y + z * w), 1 - 2 * (x * x + z * z), 2 * (y * z - x * w)],
                  [2 * (x * z - y * w), 2 * (y * z + x * w), 1 - 2 * (x * x + y * y)]])
    m = np.eye(4)
    m[:3, :3] = r * local[n]['scale']
    m[:3, 3] = local[n]['translation']
    if 'matrix' in doc['nodes'][n]:
        m = np.array(doc['nodes'][n]['matrix']).reshape(4, 4).T
    return m


parent = {c: i for i, n in enumerate(doc['nodes']) for c in n.get('children', [])}


def world(n):
    m = matrix(n)
    while n in parent:
        n = parent[n]
        m = matrix(n) @ m
    return m


for name in sys.argv[4].split(','):
    n = next(i for i, x in enumerate(doc['nodes']) if x.get('name') == name)
    p = world(n)[:3, 3]
    print(name, ','.join(f'{v:.4f}' for v in p))
