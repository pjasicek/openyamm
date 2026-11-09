"""Per clip, the rotation range (deg) of each finger joint away from its rest in an MM9 GLB. Usage: finger_range.py <glb>"""
import sys
import numpy as np
from pygltflib import GLTF2
g = GLTF2().load(sys.argv[1]); blob = g.binary_blob()
def read(i):
    a = g.accessors[i]; bv = g.bufferViews[a.bufferView]
    n = {'SCALAR': 1, 'VEC3': 3, 'VEC4': 4}[a.type]
    return np.frombuffer(blob, '<f4', a.count * n, (bv.byteOffset or 0) + (a.byteOffset or 0)).reshape(a.count, n)
rest = {i: np.array(nd.rotation or [0, 0, 0, 1]) for i, nd in enumerate(g.nodes)}
for an in g.animations:
    out = []
    for ch in an.channels:
        nm = g.nodes[ch.target.node].name
        if not any(k in nm for k in sys.argv[2].split(',')) or ch.target.path != 'rotation':
            continue
        q = read(an.samplers[ch.sampler].output); r = rest[ch.target.node]
        d = np.degrees(2 * np.arccos(np.clip(np.abs(q @ r), 0, 1)))
        out.append(f"{nm.replace('Bip01 ','')}:{d.max():.0f}")
    print(an.name, ' '.join(out))
