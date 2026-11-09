#!/usr/bin/env python3
"""Move a clip's root keys by one constant offset (MM9's run floats 5 cm over the floor). Args: in.glb out.glb Clip:dy ..."""
import sys
import numpy as np
from pygltflib import GLTF2, Accessor, BufferView
IN, OUT = sys.argv[1:3]
g = GLTF2().load(IN); blob = bytearray(g.binary_blob())
names = [n.name for n in g.nodes]
def read(i):
    a = g.accessors[i]; bv = g.bufferViews[a.bufferView]; o = (bv.byteOffset or 0) + (a.byteOffset or 0)
    return np.frombuffer(bytes(blob[o:o + 12 * a.count]), 'f4').reshape(-1, 3).copy()
for spec in sys.argv[3:]:
    clip, dy = spec.split(':')
    an = next(a for a in g.animations if a.name == clip)
    ch = next(c for c in an.channels if names[c.target.node] == 'Bip01 Pelvis' and c.target.path == 'translation')
    s = an.samplers[ch.sampler]
    v = read(s.output); v[:, 1] += float(dy)
    while len(blob) % 4: blob.append(0)
    o = len(blob); d = v.astype('f4').tobytes(); blob += d
    g.bufferViews.append(BufferView(buffer=0, byteOffset=o, byteLength=len(d)))
    g.accessors.append(Accessor(bufferView=len(g.bufferViews) - 1, componentType=5126, count=len(v), type='VEC3', min=v.min(0).tolist(), max=v.max(0).tolist()))
    s.output = len(g.accessors) - 1
g.buffers[0].byteLength = len(blob); g.set_binary_blob(bytes(blob)); g.save(OUT)
print('LOWERED', sys.argv[3:])
