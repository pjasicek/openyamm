#!/usr/bin/env python3
"""A constant abduction of both upper arms in every clip: our thighs and flanks are wider than MM9's, whose hands hang tight against them. One rotation for the whole clip, about the body's forward axis in the clavicle's frame: no new motion, no jitter. Args: <in glb> <out glb> <degrees>"""
import sys
from pathlib import Path
import numpy as np
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'claude_shared' / 'floor'))
from glb_pose import Glb, Model
from pygltflib import GLTF2
IN, OUT, DEG = sys.argv[1], sys.argv[2], float(sys.argv[3])
m = Model(Glb(IN)); names = [n.get('name') for n in m.glb.json['nodes']]; W = m.world({})
g = GLTF2().load(IN); blob = bytearray(g.binary_blob())
def qm(a, b):
    x1, y1, z1, w1 = a; x2, y2, z2, w2 = b.T
    return np.c_[w1 * x2 + x1 * w2 + y1 * z2 - z1 * y2, w1 * y2 - x1 * z2 + y1 * w2 + z1 * x2, w1 * z2 + x1 * y2 - y1 * x2 + z1 * w2, w1 * w2 - x1 * x2 - y1 * y2 - z1 * z2]
for s, sg in (('L', 1), ('R', -1)):
    i = names.index(f'Bip01 {s} UpperArm'); pa = names.index(f'Bip01 {s} Clavicle')
    ax = np.linalg.inv(W[pa][:3, :3]) @ np.array([0, 0, sg * 1.0]); ax /= np.linalg.norm(ax)
    h = np.radians(DEG) / 2; q = np.r_[ax * np.sin(h), np.cos(h)]
    n = 0
    for an in g.animations:
        for c in an.channels:
            if c.target.node == i and c.target.path == 'rotation':
                a = g.accessors[an.samplers[c.sampler].output]; bv = g.bufferViews[a.bufferView]
                o = (bv.byteOffset or 0) + (a.byteOffset or 0)
                v = np.frombuffer(bytes(blob[o:o + 16 * a.count]), 'f4').reshape(-1, 4).astype(float)
                blob[o:o + 16 * a.count] = qm(q, v).astype('f4').tobytes(); n += 1
    print('ARMOUT', s, n)
g.set_binary_blob(bytes(blob)); g.save(OUT)
