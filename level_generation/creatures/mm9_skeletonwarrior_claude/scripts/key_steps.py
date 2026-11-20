#!/usr/bin/env python3
"""Rotation step between MM9 keys per joint, to find outlier keys. Args: <glb> <clip> <joint substrings...>"""
import sys
import numpy as np
from pygltflib import GLTF2
g = GLTF2().load(sys.argv[1]); blob = g.binary_blob()
def acc(i):
    a = g.accessors[i]; bv = g.bufferViews[a.bufferView]; n = {'SCALAR': 1, 'VEC3': 3, 'VEC4': 4}[a.type]
    return np.frombuffer(blob, 'f4', a.count * n, (bv.byteOffset or 0) + (a.byteOffset or 0)).reshape(a.count, n)
an = next(a for a in g.animations if a.name == sys.argv[2])
for ch in an.channels:
    nm = g.nodes[ch.target.node].name
    if ch.target.path != 'rotation' or not any(s in nm for s in sys.argv[3:]): continue
    s = an.samplers[ch.sampler]; t = acc(s.input)[:, 0]; q = acc(s.output).copy()
    d = np.abs((q[1:] * q[:-1]).sum(1)); ang = np.degrees(2 * np.arccos(np.clip(d, 0, 1)))
    print(nm, 'keys', len(t), 'dt', np.round(np.diff(t).max(), 3), 'steps deg', np.round(ang, 0).astype(int).tolist())
