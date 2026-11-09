#!/usr/bin/env python3
"""Move Socket_Eye_Left/Right forward (Blender -Y, the ghost's facing) so the engine's eye embers start in front of the
eye domes (add_eyes.py) instead of inside them: rest world y -> REA_EYE_SOCKET_Y (default -.050).
Usage: eye_sockets.py <glb> (in place)"""
import os, sys
from pathlib import Path
import numpy as np
P = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(P.parent / 'claude_shared')); import region_variants as R  # noqa: E402
path = Path(sys.argv[1]); doc, binary = R.read_glb(path); target = float(os.environ.get('REA_EYE_SOCKET_Y', '-.050'))


def trs(n):
    t = np.array(n.get('translation', [0, 0, 0])); x, y, z, w = n.get('rotation', [0, 0, 0, 1]); s = n.get('scale', [1, 1, 1])
    r = np.array([[1 - 2 * (y * y + z * z), 2 * (x * y - z * w), 2 * (x * z + y * w)],
                  [2 * (x * y + z * w), 1 - 2 * (x * x + z * z), 2 * (y * z - x * w)],
                  [2 * (x * z - y * w), 2 * (y * z + x * w), 1 - 2 * (x * x + y * y)]])
    m = np.eye(4); m[:3, :3] = r * s; m[:3, 3] = t; return m


parent = {c: i for i, n in enumerate(doc['nodes']) for c in n.get('children', [])}


def world(i):
    m = trs(doc['nodes'][i])
    while i in parent:
        i = parent[i]; m = trs(doc['nodes'][i]) @ m
    return m


for i, n in enumerate(doc['nodes']):
    if n.get('name') in ('Socket_Eye_Left', 'Socket_Eye_Right'):
        w = world(i)[:3, 3]; blender_y = -w[2]               # glTF (x, y, z) = Blender (x, z, -y)
        delta = np.array([0, 0, -(target - blender_y)])      # world glTF delta
        local = np.linalg.inv(world(parent[i])[:3, :3]) @ delta if i in parent else delta
        n['translation'] = (np.array(n.get('translation', [0, 0, 0])) + local).tolist()
        print('SOCKET', n['name'], 'blender y', round(blender_y, 4), '->', round(-world(i)[2, 3], 4))
R.write_glb(path, doc, binary)
