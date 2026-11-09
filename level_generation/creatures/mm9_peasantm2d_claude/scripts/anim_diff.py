"""Compare the animations of two GLBs channel by channel (same node names): max abs difference per clip. Args: <a.glb> <b.glb>"""
import sys, numpy as np
from pygltflib import GLTF2
def load(p):
    g = GLTF2().load(p); blob = g.binary_blob()
    def acc(i):
        a = g.accessors[i]; bv = g.bufferViews[a.bufferView]
        n = {'SCALAR': 1, 'VEC2': 2, 'VEC3': 3, 'VEC4': 4}[a.type]
        return np.frombuffer(blob, 'f4', a.count * n, (bv.byteOffset or 0) + (a.byteOffset or 0)).reshape(a.count, n)
    out = {}
    for an in g.animations:
        d = {}
        for ch in an.channels:
            s = an.samplers[ch.sampler]; d[(g.nodes[ch.target.node].name, ch.target.path)] = (acc(s.input), acc(s.output))
        out[an.name] = d
    return out
A, B = load(sys.argv[1]), load(sys.argv[2])
for name in sorted(set(A) | set(B)):
    if name not in A or name not in B: print(name, 'only in', 'A' if name in A else 'B'); continue
    a, b = A[name], B[name]; mx = 0.0; miss = len(set(a) ^ set(b))
    for k in set(a) & set(b):
        if a[k][0].shape != b[k][0].shape or a[k][1].shape != b[k][1].shape: mx = float('inf'); continue
        mx = max(mx, float(np.abs(a[k][0] - b[k][0]).max()), float(np.abs(a[k][1] - b[k][1]).max()))
    print(f'{name:12s} channels {len(a)}/{len(b)} missing {miss} max diff {mx:.2e}')
